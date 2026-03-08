#!/usr/bin/env python3
"""
Persona Agent — orchestrates all Exa + GMI steps.
Emits JSON events to stdout for SSE streaming.
Usage:
  python run.py generate <name> <context> <url1> [url2] [url3]
  python run.py nudge <nudge_id>
"""

import sys
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Load .env.local if API keys not in environment (e.g. IDE, fresh shell)
if "GMI_API_KEY" not in os.environ or "EXA_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    for path in [
        Path(__file__).parent.parent / ".env.local",  # project root
        Path(__file__).parent / ".env.local",         # agent/
    ]:
        if path.exists():
            load_dotenv(path)
            break

from steps.scrape         import scrape_links
from steps.search         import search_public_presence
from steps.answer         import answer_questions
from steps.research       import research_person
from steps.infer_vibe     import infer_vibe
from steps.generate_images import generate_portfolio_images
from steps.generate_html  import generate_html
from steps.nudge          import apply_nudge, NUDGE_OPTIONS

# ── Setup ────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── SSE helpers ───────────────────────────────────────────────────────
def emit(event: str, **data):
    payload = {"event": event, **data}
    print(json.dumps(payload), flush=True)

def step_start(step: str, label: str, detail: str = ""):
    emit("step_start", step=step, label=label, detail=detail)

def step_done(step: str, label: str, summary: str = "", data: dict = None):
    emit("step_done", step=step, label=label, summary=summary, data=data or {})

def step_error(step: str, error: str):
    emit("step_error", step=step, error=error)

# ── Generate flow ─────────────────────────────────────────────────────
def run_generate(name: str, context: str, urls: list[str]):
    emit("agent_start", name=name, urls=urls)

    profile = {"name": name, "context": context}

    # ── PARALLEL: Contents + Search + Answer ─────────────────────────
    step_start("contents", "Scraping your links", f"{len(urls)} URLs via Exa Contents API")
    step_start("search",   "Searching your public presence", "Exa Search API")
    step_start("answer",   "Answering targeted questions", "Exa Answer API")

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_contents = executor.submit(scrape_links, urls)
        f_search   = executor.submit(search_public_presence, name, context)
        f_answers  = executor.submit(answer_questions, name)

        results = {}
        for future, key in [(f_contents, "contents"), (f_search, "search"), (f_answers, "answer")]:
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {}
                step_error(key, str(e))

    # Contents done
    contents_data = results.get("contents", {})
    step_done(
        "contents", "Links scraped",
        summary=f"{len([u for u in contents_data if u != 'error'])} pages extracted",
        data={"urls": list(contents_data.keys())}
    )
    profile["link_summaries"] = {
        url: d.get("summary", "") for url, d in contents_data.items() if isinstance(d, dict)
    }
    profile["link_text_snippets"] = {
        url: (d.get("text", ""))[:1500] for url, d in contents_data.items() if isinstance(d, dict)
    }

    # Search done
    search_data = results.get("search", [])
    step_done(
        "search", "Public presence mapped",
        summary=f"{len(search_data)} mentions found",
        data={"count": len(search_data)}
    )
    profile["public_mentions"] = search_data[:8]

    # Answer done
    qa_data = results.get("answer", {})
    answered = [k for k, v in qa_data.items() if "unavailable" not in v]
    step_done(
        "answer", "Questions answered",
        summary=f"{len(answered)}/5 questions resolved",
        data={"answered": answered}
    )
    profile["targeted_qa"] = qa_data

    # ── RESEARCH (slower, runs after parallel batch) ───────────────────
    step_start("research", "Deep profiling", "Exa Research API — structured JSON extraction")
    research_data = research_person(name, context, timeout=90)
    if "error" in research_data:
        step_error("research", research_data["error"])
    else:
        step_done(
            "research", "Profile structured",
            summary=f"Found: {', '.join(k for k, v in research_data.items() if v)}",
            data={"fields": list(research_data.keys())}
        )
    profile["deep_research"] = research_data

    # Save profile
    profile_path = OUTPUT_DIR / "profile.json"
    profile_path.write_text(json.dumps(profile, indent=2))
    emit("profile_saved", path=str(profile_path))

    # ── VIBE INFERENCE ────────────────────────────────────────────────
    step_start("vibe", "Inferring your aesthetic", "GMI analyzing personality signals")
    try:
        vibe = infer_vibe(profile)
        vibe_path = OUTPUT_DIR / "vibe.json"
        vibe_path.write_text(json.dumps(vibe, indent=2))
        step_done("vibe", "Aesthetic defined", summary=vibe.get("vibe_summary", ""))
        emit("vibe_inferred", vibe=vibe)
    except Exception as e:
        step_error("vibe", str(e))
        vibe = {
            "vibe_summary": "Clean, professional dark portfolio",
            "theme": "dark",
            "color_palette": {"background": "#0a0a0a", "surface": "#111", "primary_text": "#f0f0f0",
                              "secondary_text": "#888", "accent": "#6366f1", "accent_secondary": "#8b5cf6"},
            "font_suggestions": {"display": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "layout_style": "minimal clean",
            "motion_style": "subtle fades",
            "personality_match": "professional",
            "tagline_style": "one punchy line",
            "typography_style": "clean sans"
        }

    # ── IMAGE GENERATION (optional, in parallel with HTML prep) ─────────
    images: list[str] = []
    try:
        images = generate_portfolio_images(vibe, profile.get("name", ""), max_images=2)
    except Exception:
        pass  # continue without images

    # ── HTML GENERATION ───────────────────────────────────────────────
    step_start("generate", "Generating your portfolio", "GMI building the HTML")
    try:
        html = generate_html(profile, vibe, images=images if images else None)
        html_path = OUTPUT_DIR / "portfolio.html"
        html_path.write_text(html)
        step_done("generate", "Portfolio ready", summary="HTML generated successfully")
        emit("portfolio_ready", html=html)
    except Exception as e:
        step_error("generate", str(e))

    emit("agent_done")

# ── Nudge flow ────────────────────────────────────────────────────────
def run_nudge(nudge_id: str):
    try:
        profile = json.loads((OUTPUT_DIR / "profile.json").read_text())
        vibe    = json.loads((OUTPUT_DIR / "vibe.json").read_text())
        current_html = (OUTPUT_DIR / "portfolio.html").read_text()
    except FileNotFoundError as e:
        emit("nudge_error", error=f"Missing output file: {e}")
        return

    emit("nudge_start", nudge_id=nudge_id)
    try:
        new_html = apply_nudge(nudge_id, current_html, profile, vibe)
        (OUTPUT_DIR / "portfolio.html").write_text(new_html)
        emit("nudge_done", nudge_id=nudge_id, html=new_html)
    except Exception as e:
        emit("nudge_error", error=str(e))

# ── Entry point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"event": "error", "message": "No command provided"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "generate":
        # argv: generate <name> <context> <url1> [url2...]
        if len(sys.argv) < 4:
            print(json.dumps({"event": "error", "message": "Usage: run.py generate <name> <context> <urls...>"}))
            sys.exit(1)
        name    = sys.argv[2]
        context = sys.argv[3]
        urls    = sys.argv[4:]
        run_generate(name, context, urls)

    elif command == "nudge":
        if len(sys.argv) < 3:
            print(json.dumps({"event": "error", "message": "Usage: run.py nudge <nudge_id>"}))
            sys.exit(1)
        run_nudge(sys.argv[2])

    elif command == "nudge_options":
        print(json.dumps({"event": "nudge_options", "options": NUDGE_OPTIONS}))

    else:
        print(json.dumps({"event": "error", "message": f"Unknown command: {command}"}))
        sys.exit(1)
