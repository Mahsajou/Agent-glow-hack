# Persona — Portfolio Generator Agent

## What this is
A Next.js app that generates a personalized portfolio from a person's name. The agent extracts data for 12 portfolio aspects (identity, skills, projects, process, impact, range, depth, credibility, journey, personality, communication, future), infers aesthetic and content structure, and produces a bespoke HTML portfolio. See [docs/portfolio-framework.md](docs/portfolio-framework.md).

## Pipeline (sequential, file-based)
1. **Search** — Exa Search → `search.json`
2. **Contents** — Exa Contents → `contents.json`
3. **Research** — Exa Research → `research.json`
4. **Vibe** — GMI LLM → `vibe.json`
5. **Symbol** — GMI Image → `symbol.png`
6. **Images** — GMI Image → `banner.png`, `moodboard.png`
7. **HTML** — LLM-generated → `portfolio.html`

## Stack
- Frontend: Next.js 14, React, Tailwind CSS
- Agent: Python 3 + Temporal (optional)
- APIs: Exa (agent/lib/exa_client), GMI Cloud (agent/lib/gmi_client)

## Key files
```
agent/lib/exa_client.py   — Exa: search, get_contents, research
agent/lib/gmi_client.py   — GMI: LLM + Image
agent/agents/             — search, contents, research, vibe, symbol, images, html, nudge
agent/activities/         — Temporal activities
agent/workflows/          — PersonaGenerateWorkflow
agent/run.py              — Temporal worker (worker | start)
agent/templates/          — portfolio.html
agent/output/             — search.json, contents.json, research.json, vibe.json, symbol.png, banner.png, moodboard.png, portfolio.html
```

## Usage
```bash
# Temporal
cd agent && python run.py worker   # run worker
cd agent && python run.py start "Jane Doe" "ML engineer"  # start workflow
```

## Environment
Requires EXA_API_KEY and GMI_API_KEY in .env.local
Optional: LOG_LEVEL (debug, info, warn, error) — controls agent log verbosity; default info

### Storage backend
Workflow artifacts (search.json, portfolio.html, etc.) are stored via `agent/lib/storage.py`.

- **STORAGE_BACKEND** — `fs` (default) or `s3`
- **fs**: Uses `output_dir` as the local path
- **s3**: Uses `output_dir` as the key prefix. Requires **S3_BUCKET**; optionally **S3_REGION**, **S3_ENDPOINT_URL** (for MinIO)

For Temporal workflows: `output_dir = base_prefix/{run_id}` (run_id from Temporal) so each run has isolated storage. Nudge requires `output_dir` from the generate result.
- **MinIO**: Run `docker compose up -d` for MinIO. Set:
  ```
  STORAGE_BACKEND=s3
  S3_BUCKET=persona
  S3_ENDPOINT_URL=http://localhost:9000
  AWS_ACCESS_KEY_ID=minioadmin
  AWS_SECRET_ACCESS_KEY=minioadmin
  ```
