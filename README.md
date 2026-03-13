# Persona
**Drop your links. We figure out the rest.**

An agent-powered portfolio generator. Paste your GitHub, LinkedIn, personal site — Persona researches who you are, infers your aesthetic, and generates a bespoke portfolio that actually sounds like you.

## How it works

```
Your links + name
      ↓
Exa Contents API   — scrapes your provided links
Exa Search API     — finds public mentions you didn't link
Exa Answer API     — answers targeted questions about you
Exa Research API   — deep structured profile extraction
      ↓
OpenAI (creative director)  — infers your visual aesthetic from personality signals
OpenAI (frontend dev)       — generates a bespoke HTML portfolio
      ↓
Live preview + one-click refinements
```

## Quick start

```bash
# 1. Install dependencies
npm install
pip install -r agent/requirements.txt

# 2. Add API keys
cp .env.local.example .env.local
# Edit .env.local with your OPENAI_API_KEY, EXA_API_KEY, and GMI_API_KEY

# 3. Run
npm run dev
# Open http://localhost:3000
```

## Tech
- **Next.js 14** — App Router, API routes with SSE streaming
- **Exa** — 5 APIs for research (Contents, Search, Answer, Research, Websets)
- **OpenAI** — vibe inference + HTML generation (LLM)
- **GMI Cloud (Gemini)** — symbol, banner, moodboard images
- **AdaL CLI** — development orchestration
