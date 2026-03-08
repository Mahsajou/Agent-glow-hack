#!/usr/bin/env python3
"""
Persona Agent — sequential pipeline: Search → Contents → Research → Vibe → Images → HTML.
Emits JSON events to stdout for SSE streaming.
Usage:
  python run.py generate <name> <context>
  python run.py nudge <nudge_id>
"""

import sys
import json
import base64
from pathlib import Path

if "GMI_API_KEY" not in __import__("os").environ or "EXA_API_KEY" not in __import__("os").environ:
    from dotenv import load_dotenv
    for p in [Path(__file__).parent.parent / ".env.local", Path(__file__).parent / ".env.local"]:
        if p.exists():
            load_dotenv(p)
            break

from steps.search import run_search
from steps.contents import run_contents
from steps.research import run_research
from steps.infer_vibe import run_infer_vibe
from steps.generate_symbol import run_generate_symbol
from steps.generate_images import run_generate_images
from steps.generate_html import run_generate_html
from steps.nudge import apply_nudge, NUDGE_OPTIONS

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def emit(event: str, **data):
    print(json.dumps({"event": event, **data}), flush=True)


def step_start(step: str, label: str, detail: str = ""):
    emit("step_start", step=step, label=label, detail=detail)


def step_done(step: str, label: str, summary: str = "", data: dict = None):
    emit("step_done", step=step, label=label, summary=summary, data=data or {})


def step_error(step: str, error: str):
    emit("step_error", step=step, error=error)


def run_generate(name: str, context: str):
    emit("agent_start", name=name, urls=[])

    # 1. Search
    search_path = OUTPUT_DIR / "search.json"
    step_start("search", "Searching", "Exa Search — finding public presence")
    if search_path.exists():
        search_data = json.loads(search_path.read_text())
        urls = search_data.get("urls", [])
        step_done("search", "Search done", summary=f"{len(urls)} URLs (cached)", data={"count": len(urls)})
    else:
        try:
            search_data = run_search(name, context, search_path)
            urls = search_data.get("urls", [])
            step_done("search", "Search done", summary=f"{len(urls)} URLs found", data={"count": len(urls)})
        except Exception as e:
            step_error("search", str(e))
            emit("agent_done")
            return

    # 2. Contents
    contents_path = OUTPUT_DIR / "contents.json"
    step_start("contents", "Fetching contents", "Exa Contents — scraping URLs from search")
    if contents_path.exists():
        contents_data = json.loads(contents_path.read_text())
        cnt = contents_data.get("contents", {})
        n = sum(1 for v in cnt.values() if isinstance(v, dict) and "error" not in v)
        step_done("contents", "Contents saved", summary=f"{n} pages (cached)", data={"urls": list(cnt.keys())})
    else:
        try:
            contents_data = run_contents(search_path, contents_path)
            cnt = contents_data.get("contents", {})
            n = sum(1 for v in cnt.values() if isinstance(v, dict) and "error" not in v)
            step_done("contents", "Contents saved", summary=f"{n} pages extracted", data={"urls": list(cnt.keys())})
        except Exception as e:
            step_error("contents", str(e))
            emit("agent_done")
            return

    # 3. Research
    research_path = OUTPUT_DIR / "research.json"
    step_start("research", "Deep research", "Exa Research — exploring web, synthesizing profile")
    if research_path.exists():
        research_data = json.loads(research_path.read_text())
        if research_data.get("error"):
            step_error("research", research_data["error"])
        else:
            step_done("research", "Research saved", summary="Profile (cached)", data={"fields": list(research_data.keys())})
    else:
        try:
            research_data = run_research(name, context, research_path)
            if research_data.get("error"):
                step_error("research", research_data["error"])
            else:
                step_done("research", "Research saved", summary="Profile extracted", data={"fields": list(research_data.keys())})
        except Exception as e:
            step_error("research", str(e))
            research_data = {}

    # 4. Infer Vibe
    vibe_path = OUTPUT_DIR / "vibe.json"
    step_start("vibe", "Inferring aesthetic", "GMI — inferring vibe from research")
    if vibe_path.exists():
        vibe = json.loads(vibe_path.read_text())
        step_done("vibe", "Vibe saved", summary=vibe.get("vibe_summary", "")[:80] + " (cached)")
        emit("vibe_inferred", vibe=vibe)
    else:
        try:
            vibe = run_infer_vibe(research_path, vibe_path)
            step_done("vibe", "Vibe saved", summary=vibe.get("vibe_summary", "")[:80])
            emit("vibe_inferred", vibe=vibe)
        except Exception as e:
            step_error("vibe", str(e))
            vibe = {
                "vibe_summary": "Clean, professional dark portfolio",
                "theme": "dark",
                "color_palette": {"background": "#0a0a0a", "surface": "#111", "primary_text": "#f0f0f0",
                                 "secondary_text": "#888", "accent": "#6366f1", "accent_secondary": "#8b5cf6"},
                "font_suggestions": {"display": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
                "layout_style": "minimal",
                "motion_style": "subtle fades",
                "personality_match": "professional",
                "tagline_style": "one punchy line",
                "typography_style": "clean sans",
            }
            vibe_path.write_text(json.dumps(vibe, indent=2))
            emit("vibe_inferred", vibe=vibe)

    # 5. Symbol (brand mark image)
    symbol_path = OUTPUT_DIR / "symbol.png"
    symbol_uri = ""
    step_start("symbol", "Creating symbol", "GMI Image — brand mark")
    if symbol_path.exists():
        symbol_uri = f"data:image/png;base64,{base64.b64encode(symbol_path.read_bytes()).decode('ascii')}"
        step_done("symbol", "Symbol saved", summary="Brand mark (cached)")
    else:
        try:
            symbol_uri = run_generate_symbol(vibe_path, research_path, symbol_path)
            step_done("symbol", "Symbol saved", summary="Brand mark generated")
        except Exception as e:
            step_error("symbol", str(e))

    # 6. Images
    banner_path = OUTPUT_DIR / "banner.png"
    moodboard_path = OUTPUT_DIR / "moodboard.png"
    step_start("images", "Generating images", "GMI Image — banner & moodboard")
    images = []
    if banner_path.exists() or moodboard_path.exists():
        for p in [banner_path, moodboard_path]:
            if p.exists():
                b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                images.append(f"data:image/png;base64,{b64}")
        step_done("images", "Images done", summary=f"{len(images)} images (cached)")
    else:
        try:
            images, img_err = run_generate_images(vibe_path, research_path, max_images=2)
            if img_err:
                step_error("images", img_err)
            elif images:
                for i, uri in enumerate(images):
                    if uri.startswith("data:image/"):
                        _, b64 = uri.split(",", 1)
                        (OUTPUT_DIR / ("banner.png" if i == 0 else "moodboard.png")).write_bytes(base64.b64decode(b64))
                step_done("images", "Images done", summary=f"{len(images)} images saved")
            else:
                step_done("images", "Images skipped", summary="No images generated")
        except Exception as e:
            step_error("images", str(e))

    # 7. HTML
    portfolio_path = OUTPUT_DIR / "portfolio.html"
    step_start("generate", "Generating portfolio", "GMI — building HTML")
    use_cached = portfolio_path.exists()
    if use_cached and symbol_uri:
        cached = portfolio_path.read_text()
        if "brand-symbol" not in cached and "hero-banner-img" not in cached:
            use_cached = False  # Regenerate to include new banner/symbol
    if use_cached:
        html = portfolio_path.read_text()
        step_done("generate", "Portfolio ready", summary="HTML (cached)")
        emit("portfolio_ready", html=html)
    else:
        try:
            html = run_generate_html(
                research_path,
                vibe_path,
                images=images if images else None,
                symbol_img=symbol_uri if symbol_uri else None,
            )
            portfolio_path.write_text(html)
            step_done("generate", "Portfolio ready", summary="HTML generated")
            emit("portfolio_ready", html=html)
        except Exception as e:
            step_error("generate", str(e))

    emit("agent_done")


def run_nudge(nudge_id: str):
    try:
        research = json.loads((OUTPUT_DIR / "research.json").read_text())
        vibe = json.loads((OUTPUT_DIR / "vibe.json").read_text())
        current_html = (OUTPUT_DIR / "portfolio.html").read_text()
    except FileNotFoundError as e:
        emit("nudge_error", error=f"Missing file: {e}")
        return
    emit("nudge_start", nudge_id=nudge_id)
    try:
        new_html = apply_nudge(nudge_id, current_html, research, vibe)
        (OUTPUT_DIR / "portfolio.html").write_text(new_html)
        emit("nudge_done", nudge_id=nudge_id, html=new_html)
    except Exception as e:
        emit("nudge_error", error=str(e))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"event": "error", "message": "No command"}))
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "generate":
        if len(sys.argv) < 3:
            print(json.dumps({"event": "error", "message": "Usage: run.py generate <name> [context]"}))
            sys.exit(1)
        name = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        run_generate(name, context)
    elif cmd == "nudge":
        if len(sys.argv) < 3:
            print(json.dumps({"event": "error", "message": "Usage: run.py nudge <nudge_id>"}))
            sys.exit(1)
        run_nudge(sys.argv[2])
    elif cmd == "nudge_options":
        print(json.dumps({"event": "nudge_options", "options": NUDGE_OPTIONS}))
    else:
        print(json.dumps({"event": "error", "message": f"Unknown command: {cmd}"}))
        sys.exit(1)
