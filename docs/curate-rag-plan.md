# Curate Agent RAG — Final Revised Plan

Refactor the persona pipeline so RAG stores full context per run and the curate agent produces `curated.json` from retrieved RAG data plus enhancements, keeping the system context-rich without hitting token limits.

---

## 1. Problem

- **Current flow**: Curate dumps full `research.json` + full `contents.json` into one LLM prompt
- **contents.json**: `{urls: [...], contents: {url: {text, summary, highlights}}}` — `text` uncapped
- **Result**: 400 Bad Request when prompt exceeds model context limit

---

## 2. Solution

1. **Producer agents index** — Contents and Research agents write JSON and index into RAG (pgvector), scoped by `run_id`
2. **Curate only retrieves + curates** — Retrieves from RAG, adds enhancements, sends to LLM → `curated.json`
3. **Strict session isolation** — Every index/retrieve is scoped by `run_id`; no cross-session data
4. **Context-rich** — Multi-query retrieval, higher top_k, summaries + highlights + text, source metadata

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ PRODUCER AGENTS (index on write)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Contents agent   → contents.json  + index chunks to RAG (run_id)             │
│ Research agent   → research.json  + index key fields to RAG (run_id)         │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  RAG (pgvector) │
                              │  run_id scoped  │
                              │  full context   │
                              └────────┬────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ CURATE AGENT (retrieve + enhance + LLM)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Load research.json (for query + primary structure)                        │
│ 2. retrieve(run_id, queries) → top-k chunks                                  │
│ 3. Enhancements: schema, instructions, structure hints                       │
│ 4. LLM(research + chunks + enhancements) → curated.json                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Choices

| Component | Choice |
|-----------|--------|
| Vector store | **Qdrant** |
| Embedding model | **OpenAI text-embedding-3-small** (1536 dims) |
| Chunking | Per-URL: summary, highlights, text (split if >2k chars) |
| Session isolation | **run_id** on every row; all queries filter by run_id |
| Indexing | Done by Contents + Research agents; Curate does NOT index |

---

## 5. Data Model (Qdrant)

### Collection: `persona_chunks`

- **Vectors**: 1536 dims (OpenAI text-embedding-3-small), COSINE distance
- **Payload** per point: `run_id`, `url`, `chunk_index`, `chunk_text`, `metadata`
- **Filter** on retrieve: `run_id` for session isolation
- Auto-created on first `index_chunks` call

---

## 6. Indexing (Producer Agents)

### Contents agent
- Writes `contents.json` as today
- After write: `chunk_contents(contents)` → `index_chunks(run_id, chunks)`
- Chunking:
  - Summary: 1 chunk per URL
  - Highlights: 1 chunk per highlight (or batched if many)
  - Text: split if len > 2000 chars (~1500 chars, 100 overlap)

### Research agent
- Writes `research.json` as today
- After write: `chunk_research(research)` → `index_chunks(run_id, chunks)`
- Chunking: serialize key fields (bio, skills, projects, focus_areas, etc.) as text chunks

### run_id
- Extract from `output_dir`: last path segment (e.g. `persona/output/abc-123` → `abc-123`)
- Passed into both agents via activity args

---

## 7. Curate Agent Flow

1. **Load** `research.json`
2. **Retrieve** from RAG:
   - Multi-query: `[name + bio, skills, projects, focus_areas, ...]`
   - `retrieve(run_id, queries, top_k)` → union, dedupe by chunk id
   - top_k per query or total; target ~15–25 chunks
3. **Format** chunks for prompt: `URL: X | Source: summary/highlights/text | Content: ...`
4. **Enhancements**: schema, instructions ("merge facts, add logical links"), output format
5. **LLM** prompt:
   ```
   RESEARCH (primary structure):
   {research}

   RETRIEVED CHUNKS (evidence):
   {formatted chunks}

   ENHANCEMENTS:
   - Output schema: full_name, bio, skills, projects, ...
   - Merge facts, deduplicate, enrich from chunks
   - Add logical derived data where appropriate

   → curated.json
   ```
6. **Write** `curated.json`

---

## 8. Chunking Strategy (Context-Rich)

| Source | Strategy |
|--------|----------|
| Summary | 1 chunk per URL, high signal |
| Highlights | 1 chunk per highlight (Exa caps at 4k chars each) |
| Text | Split at ~1500 chars, 100 overlap; skip if empty |
| Research | Key fields as text: bio, skills, projects (name+description), focus_areas, etc. |

Include `url` and `source` (summary/highlights/text) in metadata so the LLM can weight and cite.

---

## 9. Query Construction (Multi-Query for Context-Rich)

Build 2–4 queries from research:
1. `{full_name} {bio}` (identity)
2. `{focus_areas} {skills} {specialization}` (expertise)
3. Project names + descriptions (truncated)
4. `{values} {personal_philosophy}` (optional)

Run retrieve for each, union results, dedupe by chunk id. Increases recall.

---

## 10. Module Structure

```
agent/
  lib/
    rag.py                    # NEW
      - embed(text) -> list[float]
      - chunk_contents(contents) -> list[dict]
      - chunk_research(research) -> list[dict]
      - index_chunks(run_id, chunks)
      - retrieve(run_id, queries, top_k) -> list[dict]
      - delete_run(run_id)     # optional cleanup
  agents/
    contents.py               # MODIFY: add index_chunks after write
    research.py               # MODIFY: add index_chunks after write
    curate.py                 # MODIFY: retrieve + enhancements → LLM
  activities/
    generate_activities.py    # MODIFY: pass run_id, ensure curate gets run_id
```

---

## 11. Implementation Phases

### Phase 1: RAG library (`agent/lib/rag.py`)
- [ ] `embed(text: str) -> list[float]` — OpenAI embeddings API
- [ ] `chunk_contents(contents: dict) -> list[dict]` — url, chunk_text, metadata
- [ ] `chunk_research(research: dict) -> list[dict]` — key fields as text
- [ ] `index_chunks(run_id: str, chunks: list[dict])` — embed + insert into Postgres
- [ ] `retrieve(run_id: str, queries: list[str], top_k: int) -> list[dict]` — multi-query, union, dedupe
- [ ] `delete_run(run_id: str)` — optional cleanup
- [ ] Config: RAG_DB_URL, RAG_TOP_K, OPENAI_EMBEDDING_MODEL, RAG_CHUNK_MAX_CHARS

### Phase 2: Contents agent
- [ ] Extract run_id from output_path (or receive as arg)
- [ ] After writing contents.json: call `index_chunks(run_id, chunk_contents(contents))`
- [ ] Indexing always runs (RAG always enabled)

### Phase 3: Research agent
- [ ] Receive run_id (from activity)
- [ ] After writing research.json: call `index_chunks(run_id, chunk_research(research))`
- [ ] Indexing always runs (RAG always enabled)

### Phase 4: Curate activity
- [ ] Extract run_id from output_dir
- [ ] Load research.json
- [ ] Call `retrieve(run_id, build_queries(research), top_k)` → chunks
- [ ] Pass `(research, chunks)` to curate agent
- [ ] If RAG empty/unavailable: fallback to truncation (summary + truncated text per URL)

### Phase 5: Curate agent
- [ ] Signature: `run(research: dict, chunks: list[dict], output_path: Path)`
- [ ] Format chunks for prompt with URL + source + content
- [ ] Add enhancements (schema, instructions)
- [ ] LLM → parse JSON → write curated.json
- [ ] Same output schema as today

### Phase 6: Activity changes (run_id)
- [ ] Ensure contents_activity, research_activity, curate_activity receive or derive run_id
- [ ] output_dir format: `base_prefix/{run_id}` — run_id = last segment

### Phase 7: Infrastructure
- [ ] pgvector in Postgres (migration)
- [ ] requirements.txt: psycopg2-binary, pgvector
- [ ] Env vars in values.yaml / deployment

### Phase 8: Fallback and robustness
- [ ] RAG always enabled; truncation fallback when Qdrant unavailable
- [ ] If retrieve returns empty: curate uses research + truncated contents
- [ ] Log prompt size (chars/4) for monitoring

---

## 12. Config

| Env var | Description | Default |
|---------|-------------|---------|
| QDRANT_URL | Qdrant HTTP API URL | http://localhost:6333 |
| RAG_TOP_K | Total chunks to retrieve (after union) | 20 |
| RAG_TOP_K_PER_QUERY | Per-query limit (for multi-query) | 8 |
| OPENAI_EMBEDDING_MODEL | Embeddings model | text-embedding-3-small |
| RAG_CHUNK_MAX_CHARS | Max chars per text chunk | 1500 |
| RAG_CHUNK_OVERLAP | Overlap between text chunks | 100 |

---

## 13. Token Budget (approx)

- Research JSON: ~2k–10k tokens
- Retrieved chunks (20 × ~400 chars): ~2k tokens
- Enhancements + instructions: ~500 tokens
- **Total input**: ~5k–13k tokens — well under 128k
- Room to increase RAG_TOP_K if needed

---

## 14. Session Isolation (Strict)

- **run_id** is the partition: every insert and query filters by run_id
- No shared data between runs
- Cleanup: `delete_run(run_id)` after workflow completes or TTL job

---

## 15. Rollback

- Truncation fallback when Qdrant retrieve fails (curate activity)
- Keeps system working if Postgres/pgvector unavailable

---

## 16. Implementation Status

Implemented. Files changed:
- `agent/lib/rag.py` — Qdrant client (index, retrieve, chunk, embed)
- `agent/agents/contents.py` — add run_id, index after write
- `agent/agents/research.py` — add run_id, index after write
- `agent/agents/curate.py` — signature (research, chunks), format chunks, LLM
- `agent/activities/generate_activities.py` — run_id extraction, RAG retrieve / truncation fallback
- `agent/requirements.txt` — qdrant-client
- `infra/persona` — Qdrant Helm dependency, values, QDRANT_URL for worker

### Deployment
1. `helm repo add qdrant https://qdrant.github.io/qdrant-helm && helm dependency update`
2. `helm upgrade persona-infra . -f values.yaml`
3. Qdrant URL: `http://persona-infra-qdrant:6333` (in-cluster)
