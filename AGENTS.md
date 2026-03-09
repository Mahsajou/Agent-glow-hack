# Persona — Portfolio Generator Agent

## What this is
A Next.js app that generates a personalized portfolio from a person's name. The agent searches the web, fetches content, researches the person, infers their aesthetic, generates images, and produces a bespoke HTML portfolio.

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
agent/run_direct.py       — Direct pipeline (used by API for SSE)
agent/templates/          — portfolio.html
agent/output/             — search.json, contents.json, research.json, vibe.json, symbol.png, banner.png, moodboard.png, portfolio.html
```

## Usage
```bash
# Direct (no Temporal)
cd agent && python run_direct.py "Jane Doe" "ML engineer"

# Temporal
cd agent && python run.py worker   # run worker
cd agent && python run.py start "Jane Doe" "ML engineer"  # start workflow
```

## Environment
Requires EXA_API_KEY and GMI_API_KEY in .env.local
