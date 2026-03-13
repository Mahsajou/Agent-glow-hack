

**PERSONA**  
Agent-Powered Portfolio Generator

Technical Documentation  ·  v1.0

Hackathon Submission  ·  2025

Drop your links. We figure out the rest.

# **1\. Overview**

Persona is an agent-powered portfolio website generator built for the Agent-Powered Applications hackathon. It takes a person's name, a set of their links (GitHub, LinkedIn, personal site, etc.), and an optional context description — and fully autonomously generates a bespoke, production-quality HTML portfolio.

The user provides zero design input. The agent figures out who the person is, infers what visual aesthetic fits their personality and work, and generates a portfolio that genuinely sounds and looks like them.

## **1.1 Hackathon Criteria Alignment**

| ✨ Aesthetics | Live agent timeline UI, vibe card with inferred palette, sandboxed iframe preview, nudge refinement system — no chatbot interface anywhere. |
| :---- | :---- |
| **🧠 Intelligence** | 5 distinct Exa AI APIs each with a specific research role, Gemini acting as creative director then as frontend developer in two separate calls, vibe inference as an explicit structured step. |
| **⚙️ Reliability** | SSE streaming shows real-time progress instead of a spinner. Parallel API calls reduce latency. Nudges are scoped re-runs, not full regeneration. Intermediate outputs (profile.json, vibe.json) are inspectable. |

## **1.2 Sponsor Tools**

| Exa AI | Primary data source. 5 APIs — Contents, Search, Answer, Research, Websets — give the agent a complete structured picture of who the person is. |
| :---- | :---- |
| **Google Gemini** | Reasoning and generation. First call infers the visual aesthetic as a structured design spec. Second call generates the full HTML portfolio from that spec. |
| **AdaL CLI (SylphAI)** | Development orchestrator. Used to build, debug, and iterate on the agent via AGENTS.md context during the hackathon. |

# **2\. Architecture**

Persona is a Next.js 14 application with a Python agent backend. The frontend communicates with the agent through Server-Sent Events (SSE) — the API route spawns the Python process and streams its stdout line-by-line to the browser in real time.

|  | Key architectural decision The Python agent is intentionally separate from the Next.js layer. It runs as a child process, writes JSON events to stdout, and has no dependency on the web framework. This means it can be tested in isolation, debugged with AdaL, and the agent logic stays clean and portable. |
| :---- | :---- |

## **2.1 System Diagram**

|   Browser (Next.js frontend)       │       │  POST /api/generate  (SSE stream)       ▼   Next.js API Route       │  spawn child\_process       ▼   Python agent/run.py       │       ├─── \[PARALLEL\] ──────────────────────────────       │    scrape.py    →  Exa Contents API       │    search.py    →  Exa Search API       │    answer.py    →  Exa Answer API       │       ├─── \[SEQUENTIAL\] ─────────────────────────────       │    research.py  →  Exa Research API (async poll)       │       ├─── infer\_vibe.py   →  Gemini (creative director)       │       └─── generate\_html.py →  Gemini (frontend developer)                               →  portfolio.jsx |
| :---- |

## **2.2 Tech Stack**

| Next.js 14 | App Router, React Server Components, API Routes with SSE streaming |
| :---- | :---- |
| **React \+ TypeScript** | Frontend UI, typed event handling, component state management |
| **Tailwind CSS** | Utility-first styling, custom animation keyframes |
| **Python 3** | Agent orchestrator and all Exa/Gemini API calls |
| **exa-py SDK** | Official Exa AI Python client |
| **google-generativeai** | Official Google Gemini Python SDK |
| **ThreadPoolExecutor** | Parallel execution of Contents, Search, Answer APIs |

# **3\. File Structure**

| persona/ ├── agent/ │   ├── run.py                   \# Main orchestrator │   ├── requirements.txt │   └── steps/ │       ├── scrape.py            \# Exa Contents API │       ├── search.py            \# Exa Search API │       ├── answer.py            \# Exa Answer API │       ├── research.py          \# Exa Research API │       ├── infer\_vibe.py        \# Gemini: profile → design spec │       ├── generate\_html.py     \# Gemini: design spec → HTML │       └── nudge.py             \# Gemini: patch HTML sections │ ├── app/ │   ├── globals.css │   ├── layout.tsx │   ├── page.tsx                 \# Screen 1: Input form │   ├── generate/ │   │   └── page.tsx             \# Screen 2: Agent \+ Preview │   └── api/ │       ├── generate/route.ts    \# SSE: spawn generate │       └── nudge/route.ts       \# SSE: spawn nudge │ ├── components/ │   ├── AgentTimeline.tsx        \# Live step log │   ├── VibeCard.tsx             \# Inferred aesthetic display │   ├── NudgePanel.tsx           \# Refinement buttons │   └── PortfolioPreview.tsx     \# Sandboxed iframe │ ├── lib/ │   └── types.ts                 \# Shared TypeScript types │ ├── AGENTS.md                    \# AdaL CLI context file └── .env.local                   \# API keys |
| :---- |

# **4\. Agent Flow**

## **4.1 Generation Pipeline**

When the user submits their name and links, the agent runs a 6-step pipeline. Steps 1–3 run in parallel to minimize latency; steps 4–6 run sequentially as each depends on the output of the previous.

| 1 | Scrape Provided Links  Exa Contents API Fetches the full text, highlights, and a summary of each URL the user provides. Extracts up to 5,000 characters per page plus 5 key highlight sentences. Summary is specifically prompted to extract professional background, skills, personality, and writing style. |
| :---: | :---- |

| 2 | Map Public Presence  Exa Search API Runs 3 targeted queries to find public mentions, articles, talks, and interviews the user didn't link themselves. Each query returns 4 results with text and personality-focused summaries. Deduplicates across queries. |
| :---: | :---- |

| 3 | Answer Targeted Questions  Exa Answer API Asks 5 specific questions about the person: (1) notable projects, (2) core expertise, (3) measurable impact, (4) communication style and tone, (5) visual aesthetic sensibility. Each answer is stored separately in the profile. |
| :---: | :---- |

| 4 | Deep Profile Extraction  Exa Research API Creates an async research task with a structured JSON output schema. Polls every 4 seconds until complete (90s timeout). Returns clean structured data: full\_name, current\_role, company, bio, skills array, notable\_projects, education, achievements, writing\_samples, interests\_hobbies, personality\_notes. |
| :---: | :---- |

| 5 | Infer Visual Aesthetic  Gemini (creative director) Reads the full consolidated profile and acts as a creative director. Analyzes signals: domain type, writing tone from samples, personality notes, type of work, aesthetic preferences found online. Returns a structured vibe spec with exact hex colors, font names, layout style, motion style, and personality match. |
| :---: | :---- |

| 6 | Generate Portfolio JSX  Gemini (frontend developer) Takes the profile and vibe spec as a detailed creative brief and generates a complete, single-file JSX portfolio (stored as portfolio.jsx but containing full HTML markup). Imports fonts from Google Fonts, uses the exact color palette, implements scroll animations matching the motion style, includes all 5 sections, and uses only data found in the profile. |
| :---: | :---- |

## **4.2 Nudge Flow**

After generation, the user can apply targeted refinements without re-running the full pipeline. Each nudge patches only what was requested using the existing profile and vibe as context.

| Regenerate hero | Rewrites only the hero section with a more dramatic, memorable opening. |
| :---- | :---- |
| **Emphasize projects** | Expands the projects section with better visual hierarchy and more detail. |
| **Warmer tone** | Rewrites all copy to sound more human and personal, keeping the same design. |
| **New color scheme** | Keeps the layout but applies a completely different color palette. |
| **More minimal** | Strips decoration, increases whitespace, removes visual noise. |
| **Bolder & dramatic** | Amplifies typography, contrast, and visual presence throughout. |
| **Redesign skills** | Replaces the skills section with a more creative visual treatment. |

# **5\. SSE Event Protocol**

The Python agent communicates with the Next.js frontend through a simple line-by-line JSON protocol. Every line written to stdout is a JSON object. The API route wraps each as an SSE data frame. The frontend parses events and updates UI state accordingly.

## **5.1 Event Types**

| agent\_start | Agent has started. Payload: { name, urls } |
| :---- | :---- |
| **step\_start** | A step has begun. Payload: { step, label, detail } |
| **step\_done** | A step completed. Payload: { step, label, summary, data } |
| **step\_error** | A step failed (non-fatal). Payload: { step, error } |
| **profile\_saved** | profile.json written to disk. Payload: { path } |
| **vibe\_inferred** | Vibe spec ready. Payload: { vibe: { ...full vibe object } } |
| **portfolio\_ready** | HTML generated. Payload: { html: '\<full HTML string\>' } |
| **agent\_done** | All steps complete. Unlocks NudgePanel in UI. |
| **nudge\_start** | Nudge has begun. Payload: { nudge\_id } |
| **nudge\_done** | Nudge complete. Payload: { nudge\_id, html: '\<updated HTML\>' } |
| **nudge\_error** | Nudge failed. Payload: { error } |

## **5.2 Example Event Stream**

| data: {"event":"agent\_start","name":"Jane Doe","urls":\["https://github.com/..."\]}   data: {"event":"step\_start","step":"contents","label":"Scraping your links","detail":"3 URLs via Exa Contents API"} data: {"event":"step\_start","step":"search","label":"Mapping public presence","detail":"Exa Search API"} data: {"event":"step\_start","step":"answer","label":"Answering targeted Q\&A","detail":"Exa Answer API"}   data: {"event":"step\_done","step":"contents","summary":"3 pages extracted"} data: {"event":"step\_done","step":"search","summary":"8 mentions found"} data: {"event":"step\_done","step":"answer","summary":"5/5 questions resolved"}   data: {"event":"step\_start","step":"research","label":"Deep profile extraction"} data: {"event":"step\_done","step":"research","summary":"Found: full\_name, bio, skills, projects"}   data: {"event":"vibe\_inferred","vibe":{"vibe\_summary":"Dark editorial...","theme":"dark",...}}   data: {"event":"portfolio\_ready","html":"\<\!DOCTYPE html\>..."} data: {"event":"agent\_done"} |
| :---- |

# **6\. Data Structures**

## **6.1 Profile Object  (agent/output/profile.json)**

The consolidated research artifact built by run.py after all Exa steps complete. Used as the source of truth for both vibe inference and HTML generation.

| {   "name": "Jane Doe",   "context": "ML engineer at a startup",   "link\_summaries": {     "https://github.com/janedoe": "Summary of GitHub profile..."   },   "link\_text\_snippets": {     "https://github.com/janedoe": "Raw text up to 1500 chars..."   },   "public\_mentions": \[     { "url": "...", "title": "...", "snippet": "...", "summary": "..." }   \],   "targeted\_qa": {     "projects":    "Most notable projects...",     "expertise":   "Core technical skills...",     "impact":      "Measurable achievements...",     "personality": "Communication style...",     "aesthetics":  "Visual design sensibility..."   },   "deep\_research": {     "full\_name": "Jane Doe",     "current\_role": "Senior ML Engineer",     "company": "Acme AI",     "bio": "...",     "skills": \["Python", "PyTorch", "LLMs"\],     "notable\_projects": \["Project A", "Project B"\],     "education": "MIT, CS",     "achievements": \[...\],     "writing\_samples": \[...\],     "interests\_hobbies": \[...\],     "personality\_notes": "Precise, understated, technical writer"   } } |
| :---- |

## **6.2 Vibe Object  (agent/output/vibe.json)**

The structured design spec produced by infer\_vibe.py. Acts as the creative brief passed to generate\_html.py.

| {   "vibe\_summary": "Dark editorial — precise and understated, like a researcher who ships",   "theme": "dark",   "typography\_style": "technical mono with editorial serif accents",   "color\_palette": {     "background": "\#0a0a0a",     "surface": "\#111111",     "primary\_text": "\#e8e4dc",     "secondary\_text": "\#555555",     "accent": "\#c8f050",     "accent\_secondary": "\#ff6b35"   },   "layout\_style": "dense technical grid",   "motion\_style": "subtle fades only",   "personality\_match": "precise and understated",   "font\_suggestions": {     "display": "Syne",     "body": "Inter",     "mono": "JetBrains Mono"   },   "tagline\_style": "one punchy technical descriptor" } |
| :---- |

# **7\. UI Components**

## **7.1 Screen 1 — Input Form (app/page.tsx)**

The entry point. Minimal by design — three fields only. Validates that at least one URL is present before enabling submission. On submit, encodes all inputs as URL search params and navigates to /generate. No API call is made from this screen.

| Your name | Required. Text field. Passed as-is to the agent. |
| :---- | :---- |
| **Links** | At least one required. Up to N URLs. Add/remove dynamically. Validated as non-empty strings. |
| **Additional context** | Optional. Free text. E.g. 'ML engineer at a startup, 5 years exp'. Passed to all Exa queries. |

## **7.2 Screen 2 — Generate & Preview (app/generate/page.tsx)**

The main experience. Split layout: left panel shows agent state, right panel shows the portfolio. Opens an SSE stream to /api/generate immediately on mount. All UI updates are driven by SSE events.

| AgentTimeline | Shows each of the 6 steps with status (idle/running/done/error), the step label, detail text, API badge, and summary on completion. Steps animate in as they change state. |
| :---- | :---- |
| **VibeCard** | Appears when vibe\_inferred fires. Shows the vibe summary sentence, hex color swatches with hover tooltips, font and layout tags, and the personality match label. |
| **NudgePanel** | Appears only after agent\_done fires. 7 buttons for targeted refinements. Disabled as a group while a nudge is in progress. |
| **PortfolioPreview** | Sandboxed iframe that renders the generated HTML. Appears when portfolio\_ready fires. Shows opacity 50% while a nudge is applying. Download and open-in-new-tab buttons in the header. |

# **8\. Setup & Running**

## **8.1 Prerequisites**

* Node.js 18+

* Python 3.10+

* Exa AI API key — dashboard.exa.ai

* Google Gemini API key — aistudio.google.com

## **8.2 Install**

| \# Clone and enter the project cd persona   \# Install JS dependencies npm install   \# Install Python dependencies pip install \-r agent/requirements.txt   \# Set environment variables cp env.local.example .env.local \# Edit .env.local and fill in your keys: \#   EXA\_API\_KEY=your\_exa\_key\_here \#   GEMINI\_API\_KEY=your\_gemini\_key\_here |
| :---- |

## **8.3 Run**

| npm run dev \# Open http://localhost:3000 |
| :---- |

## **8.4 Test the Agent in Isolation**

The Python agent can be run directly without the Next.js server. This is useful for debugging individual steps or testing with new profiles.

| cd agent   \# Run full generation python run.py generate 'Jane Doe' 'ML engineer' \\   https://github.com/janedoe \\   https://linkedin.com/in/janedoe   \# Inspect outputs cat output/profile.json   \# full research profile cat output/vibe.json      \# inferred design spec open output/portfolio.jsx  \# generated portfolio   \# Apply a nudge to existing output python run.py nudge colors python run.py nudge hero python run.py nudge minimal |
| :---- |

# **9\. Known Issues & Planned Improvements**

## **9.1 Reliability**

| Research API silent failure | research.py polls with time.sleep(4). If the task fails silently it just times out. Should detect status \=== 'failed' and fail fast. |
| :---- | :---- |
| **SSE buffer edge case** | The event stream buffer in page\_generate.tsx splits on \\n. Multi-line JSON could break parsing. Should accumulate until a full valid JSON line is confirmed. |
| **Gemini HTML fence leakage** | Gemini occasionally wraps HTML in \`\`\`html fences despite instructions. Strip logic exists but edge cases slip through — needs a more robust regex. |
| **Orphaned Python processes** | If the user navigates away mid-generation, the Python child process continues running. Should handle AbortSignal to kill the process on disconnect. |
| **Missing \_\_init\_\_.py** | agent/steps/ has no \_\_init\_\_.py. Python imports may fail depending on PYTHONPATH configuration. Should add \_\_init\_\_.py or restructure imports. |

## **9.2 Intelligence**

| Conditional parallel steps | All 3 parallel steps (scrape, search, answer) fire unconditionally. If scrape returns very rich data, search and answer could be skipped to save cost. |
| :---- | :---- |
| **Domain-aware vibe signals** | infer\_vibe.py prompt could weight signals more precisely. GitHub repos with design work → lean visual. ML papers → lean technical minimal. |
| **Gemini output truncation** | max\_output\_tokens is 8192\. Complex portfolios may get cut off. Consider splitting generation into sections if output approaches the limit. |

## **9.3 UX**

| Step elapsed timers | AgentTimeline should show elapsed time per step — start a timer on step\_start, display seconds on step\_done. |
| :---- | :---- |
| **Nudge skeleton state** | PortfolioPreview shows opacity 50% during nudge. Should show a proper skeleton overlay instead. |
| **Refresh re-runs agent** | If the user refreshes /generate, the agent starts over. Should detect existing output/portfolio.jsx and offer to load it. |
| **Start over button** | No way to reset and go back to the input form cleanly. Should add a 'Start over' button that clears agent output state. |
| **VibeCard animation** | VibeCard should animate in with a slide-up transition when vibe\_inferred fires, not just appear instantly. |
| **Staggered step entrance** | All AgentTimeline steps appear at once on mount. Should stagger their entrance with animation-delay for a cleaner reveal. |

# **10\. Environment Variables**

| EXA\_API\_KEY | Required. Your Exa AI API key. Get it at dashboard.exa.ai. Used by all 5 Exa step files in agent/steps/. |
| :---- | :---- |
| **GEMINI\_API\_KEY** | Required. Your Google Gemini API key. Get it at aistudio.google.com. Used by infer\_vibe.py, generate\_html.py, and nudge.py. |

Both keys are defined in .env.local at the project root and automatically passed to the spawned Python process via process.env in the Next.js API routes.

|  | Security note Never commit .env.local to version control. The file is included in .gitignore by default in Next.js projects. Only use these keys server-side — they are never exposed to the browser. |
| :---- | :---- |

Persona  ·  Built for the Agent-Powered Applications Hackathon  ·  2025

Powered by Exa AI  ·  Google Gemini  ·  AdaL CLI (SylphAI)  ·  Next.js