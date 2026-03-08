# Persona — Portfolio Generator Agent

## What this is
A Next.js app that generates a personalized portfolio from a person's name. The agent searches the web, fetches content, researches the person, infers their aesthetic, generates images, and produces a bespoke HTML portfolio.

## Pipeline (sequential, file-based)
1. **Search** — Exa Search: find URLs about the person → `search.json`
2. **Contents** — Exa Contents: fetch web content from search URLs → `contents.json`
3. **Research** — GMI LLM: synthesize professional/personal background from contents → `research.json`
4. **Infer Vibe** — GMI LLM: infer aesthetic from research → `vibe.json`
5. **Images** — GMI Image: generate banner + moodboard from vibe + research
6. **HTML** — GMI LLM: generate portfolio from research + vibe + images → `portfolio.html`

## Stack
- Frontend: Next.js 14 (App Router), React, Tailwind CSS
- Agent: Python 3 (agent/run.py), emits JSON events for SSE
- APIs: Exa (exa-py), GMI Cloud (requests for chat + image)

## Key files
```
agent/run.py              — Orchestrator, sequential pipeline
agent/steps/search.py     — Exa Search → search.json
agent/steps/contents.py   — Exa Contents → contents.json
agent/steps/research.py   — GMI: contents.json → research.json
agent/steps/infer_vibe.py — GMI: research.json → vibe.json
agent/steps/generate_images.py — GMI Image: vibe + research → banner, moodboard
agent/steps/generate_html.py   — GMI: research + vibe + images → portfolio.html
agent/steps/nudge.py      — GMI: patch sections of existing HTML
agent/output/             — search.json, contents.json, research.json, vibe.json, portfolio.html
```

## Usage
```bash
cd agent && python run.py generate "Jane Doe" "ML engineer"
```

## Environment
Requires EXA_API_KEY and GMI_API_KEY in .env.local
