# Persona — Portfolio Generator Agent

## What this is
A Next.js app that generates a personalized portfolio website from a person's links.
The agent uses 5 Exa APIs to research the person, infers their aesthetic with GMI (Gemini),
then generates a bespoke HTML portfolio.

## Stack
- Frontend: Next.js 14 (App Router), React, Tailwind CSS
- Agent: Python 3 (agent/run.py), called via child_process in API routes
- APIs: Exa (exa-py SDK), GMI Cloud / Gemini (google-genai SDK)

## Key files
```
agent/run.py              — Main Python orchestrator, emits JSON events to stdout
agent/steps/scrape.py     — Exa Contents API
agent/steps/search.py     — Exa Search API  
agent/steps/answer.py     — Exa Answer API
agent/steps/research.py   — Exa Research API (async polling)
agent/steps/infer_vibe.py — GMI: reads profile → outputs design spec JSON
agent/steps/generate_html.py — GMI: design spec + profile → full HTML portfolio
agent/steps/nudge.py      — GMI: patch specific sections of existing HTML
agent/output/             — profile.json, vibe.json, portfolio.html written here

app/api/generate/route.ts — SSE stream: spawns Python agent, forwards stdout events
app/api/nudge/route.ts    — SSE stream: spawns nudge step
app/page.tsx              — Input form (name, links, optional context)
app/generate/page.tsx     — Agent progress + preview UI
components/AgentTimeline  — Live step-by-step log
components/VibeCard       — Shows inferred aesthetic (colors, fonts, personality)
components/NudgePanel     — 7 refinement buttons
components/PortfolioPreview — Sandboxed iframe + download button
lib/types.ts              — Shared TS types for events and state
```

## SSE event protocol
The Python agent emits one JSON object per line to stdout.
The API route wraps each as `data: {...}\n\n`.
Key events:
- step_start / step_done / step_error — drive the AgentTimeline UI
- vibe_inferred — triggers VibeCard render
- portfolio_ready — triggers iframe render
- nudge_done — updates iframe with patched HTML
- agent_done — unlocks NudgePanel

## Environment
Requires EXA_API_KEY and GMI_API_KEY in .env.local

## Dev commands
```bash
# Install JS deps
npm install

# Install Python deps
pip install -r agent/requirements.txt

# Run dev server
npm run dev

# Test agent directly
cd agent && python run.py generate "Jane Doe" "ML engineer" https://github.com/janedoe
```

## Common issues & fixes
- If Research API times out: increase timeout in research.py (default 90s)
- If GMI returns markdown fences in HTML: the strip logic in generate_html.py handles this
- If SSE stream cuts off: check maxDuration in route.ts (set to 300s)
- If iframe is blank: check browser console — likely a CSP issue with the generated HTML

## Iteration workflow
1. Run the app, generate a portfolio
2. Inspect agent/output/profile.json — if sparse, add more URLs or context
3. Inspect agent/output/vibe.json — if wrong aesthetic, adjust infer_vibe.py prompt
4. Use NudgePanel buttons in UI to refine sections without full regeneration
5. Download final HTML from preview header
