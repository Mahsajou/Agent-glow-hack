#!/usr/bin/env python3
"""
Direct pipeline execution (no Temporal). For API when Temporal is not used.
Emits JSON events to stdout for SSE. Same interface as before Temporal migration.
Usage: python run_direct.py <name> [context]
"""

import base64
import json
import os
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

if "GMI_API_KEY" not in os.environ or "EXA_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    for p in [_root / ".env.local", Path(__file__).parent / ".env.local"]:
        if p.exists():
            load_dotenv(p)
            break

from agent.agents import search, contents, research, vibe, symbol, images, html, nudge

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def emit(e: str, **kw):
    print(json.dumps({"event": e, **kw}), flush=True)


def run_nudge(nudge_id: str) -> None:
    try:
        research = json.loads((OUTPUT_DIR / "research.json").read_text())
        vibe = json.loads((OUTPUT_DIR / "vibe.json").read_text())
        html = (OUTPUT_DIR / "portfolio.html").read_text()
    except FileNotFoundError as e:
        emit("nudge_error", error=f"Missing file: {e}")
        return
    emit("nudge_start", nudge_id=nudge_id)
    try:
        new_html = nudge.run(nudge_id, html, research, vibe)
        (OUTPUT_DIR / "portfolio.html").write_text(new_html)
        emit("nudge_done", nudge_id=nudge_id, html=new_html)
    except Exception as e:
        emit("nudge_error", error=str(e))


def main():
    # nudge: run_direct.py nudge <nudge_id>
    if len(sys.argv) >= 3 and sys.argv[1].lower() == "nudge":
        run_nudge(sys.argv[2])
        return

    # generate: run_direct.py <name> [context]
    name = sys.argv[1] if len(sys.argv) > 1 else ""
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    if not name:
        emit("error", message="Usage: run_direct.py <name> [context] | run_direct.py nudge <nudge_id>")
        sys.exit(1)

    emit("agent_start", name=name, urls=[])

    sp = OUTPUT_DIR / "search.json"
    emit("step_start", step="search", label="Searching", detail="Exa Search")
    try:
        if sp.exists():
            d = json.loads(sp.read_text())
            emit("step_done", step="search", label="Search done", summary=f"{len(d.get('urls', []))} URLs (cached)")
        else:
            search.run(name, context, sp)
            d = json.loads(sp.read_text())
            emit("step_done", step="search", label="Search done", summary=f"{len(d.get('urls', []))} URLs found")
    except Exception as e:
        emit("step_error", step="search", error=str(e))
        emit("agent_done")
        return

    cp = OUTPUT_DIR / "contents.json"
    emit("step_start", step="contents", label="Fetching contents", detail="Exa Contents")
    try:
        if cp.exists():
            d = json.loads(cp.read_text())
            n = sum(1 for v in d.get("contents", {}).values() if isinstance(v, dict) and "error" not in v)
            emit("step_done", step="contents", label="Contents saved", summary=f"{n} pages (cached)")
        else:
            contents.run(sp, cp)
            d = json.loads(cp.read_text())
            n = sum(1 for v in d.get("contents", {}).values() if isinstance(v, dict) and "error" not in v)
            emit("step_done", step="contents", label="Contents saved", summary=f"{n} pages")
    except Exception as e:
        emit("step_error", step="contents", error=str(e))
        emit("agent_done")
        return

    rp = OUTPUT_DIR / "research.json"
    emit("step_start", step="research", label="Deep research", detail="Exa Research")
    try:
        if rp.exists():
            d = json.loads(rp.read_text())
            if d.get("error"):
                emit("step_error", step="research", error=d["error"])
            else:
                emit("step_done", step="research", label="Research saved", summary="Profile (cached)")
        else:
            research.run(name, context, rp)
            d = json.loads(rp.read_text())
            if d.get("error"):
                emit("step_error", step="research", error=d["error"])
            else:
                emit("step_done", step="research", label="Research saved", summary="Profile")
    except Exception as e:
        emit("step_error", step="research", error=str(e))

    vp = OUTPUT_DIR / "vibe.json"
    emit("step_start", step="vibe", label="Inferring aesthetic", detail="GMI")
    try:
        if vp.exists():
            v = json.loads(vp.read_text())
            emit("vibe_inferred", vibe=v)
            emit("step_done", step="vibe", label="Vibe saved", summary=(v.get("vibe_summary", "")[:80] + " (cached)"))
        else:
            v = vibe.run(rp, vp)
            emit("vibe_inferred", vibe=v)
            emit("step_done", step="vibe", label="Vibe saved", summary=v.get("vibe_summary", "")[:80])
    except Exception as e:
        emit("step_error", step="vibe", error=str(e))
        v = json.loads(vp.read_text()) if vp.exists() else {}

    sym_uri = ""
    sp_img = OUTPUT_DIR / "symbol.png"
    emit("step_start", step="symbol", label="Creating symbol", detail="GMI Image")
    try:
        if sp_img.exists():
            sym_uri = f"data:image/png;base64,{base64.b64encode(sp_img.read_bytes()).decode('ascii')}"
            emit("step_done", step="symbol", label="Symbol saved", summary="Brand mark (cached)")
        else:
            sym_uri = symbol.run(vp, rp, sp_img)
            emit("step_done", step="symbol", label="Symbol saved", summary="Brand mark")
    except Exception as e:
        emit("step_error", step="symbol", error=str(e))

    imgs = []
    bp, mp = OUTPUT_DIR / "banner.png", OUTPUT_DIR / "moodboard.png"
    emit("step_start", step="images", label="Generating images", detail="GMI Image")
    try:
        if bp.exists() or mp.exists():
            for p in [bp, mp]:
                if p.exists():
                    imgs.append(f"data:image/png;base64,{base64.b64encode(p.read_bytes()).decode('ascii')}")
            emit("step_done", step="images", label="Images done", summary=f"{len(imgs)} images (cached)")
        else:
            imgs, err = images.run(vp, rp, OUTPUT_DIR, max_images=2)
            if err:
                emit("step_error", step="images", error=err)
            elif imgs:
                emit("step_done", step="images", label="Images done", summary=f"{len(imgs)} images")
            else:
                emit("step_done", step="images", label="Images skipped", summary="No images")
    except Exception as e:
        emit("step_error", step="images", error=str(e))

    hp = OUTPUT_DIR / "portfolio.html"
    emit("step_start", step="generate", label="Generating portfolio", detail="HTML")
    try:
        use_cached = hp.exists()
        if use_cached and (sym_uri or imgs):
            c = hp.read_text()
            if "brand-symbol" not in c and "hero-banner" not in c:
                use_cached = False
        if use_cached:
            h = hp.read_text()
            emit("portfolio_ready", html=h)
            emit("step_done", step="generate", label="Portfolio ready", summary="HTML (cached)")
        else:
            h = html.run(rp, vp, hp, images=imgs or None, symbol_img=sym_uri or None)
            emit("portfolio_ready", html=h)
            emit("step_done", step="generate", label="Portfolio ready", summary="HTML")
    except Exception as e:
        emit("step_error", step="generate", error=str(e))

    emit("agent_done")


if __name__ == "__main__":
    main()
