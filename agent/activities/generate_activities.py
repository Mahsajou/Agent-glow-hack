"""Temporal activities for Persona portfolio generation."""

import base64
import json
from pathlib import Path

from temporalio import activity

from agent.agents import (
    search as search_agent,
    contents as contents_agent,
    research as research_agent,
    vibe as vibe_agent,
    symbol as symbol_agent,
    images as images_agent,
    html as html_agent,
)


def _out(output_dir: str) -> Path:
    return Path(output_dir)


@activity.defn
async def search_activity(name: str, context: str, output_dir: str) -> dict:
    """Search for person's public presence via Exa. Output: search.json."""
    activity.logger.info("Running search for %s", name)
    p = _out(output_dir) / "search.json"
    if p.exists():
        return json.loads(p.read_text())
    return search_agent.run(name, context, p)


@activity.defn
async def contents_activity(output_dir: str) -> dict:
    """Fetch page contents via Exa Contents. Output: contents.json."""
    out = _out(output_dir)
    search_path = out / "search.json"
    contents_path = out / "contents.json"
    if contents_path.exists():
        return json.loads(contents_path.read_text())
    return contents_agent.run(search_path, contents_path)


@activity.defn
async def research_activity(name: str, context: str, output_dir: str) -> dict:
    """Deep research via Exa Research. Output: research.json."""
    activity.logger.info("Running research for %s", name)
    out = _out(output_dir)
    rp = out / "research.json"
    if rp.exists():
        return json.loads(rp.read_text())
    return research_agent.run(name, context, rp)


@activity.defn
async def vibe_activity(output_dir: str) -> dict:
    """Infer aesthetic from research. Output: vibe.json."""
    out = _out(output_dir)
    vp = out / "vibe.json"
    rp = out / "research.json"
    if vp.exists():
        return json.loads(vp.read_text())
    return vibe_agent.run(rp, vp)


@activity.defn
async def symbol_activity(output_dir: str) -> str:
    """Generate brand symbol image. Output: symbol.png. Returns data URI."""
    out = _out(output_dir)
    vp, rp, sp = out / "vibe.json", out / "research.json", out / "symbol.png"
    if sp.exists():
        return f"data:image/png;base64,{base64.b64encode(sp.read_bytes()).decode('ascii')}"
    return symbol_agent.run(vp, rp, sp)


@activity.defn
async def images_activity(output_dir: str) -> tuple[list[str], str | None]:
    """Generate banner and moodboard images. Returns (data_uris, error)."""
    out = _out(output_dir)
    vp, rp = out / "vibe.json", out / "research.json"
    banner, mood = out / "banner.png", out / "moodboard.png"
    imgs: list[str] = []
    if banner.exists():
        imgs.append(f"data:image/png;base64,{base64.b64encode(banner.read_bytes()).decode('ascii')}")
    if mood.exists():
        imgs.append(f"data:image/png;base64,{base64.b64encode(mood.read_bytes()).decode('ascii')}")
    if imgs:
        return imgs, None
    imgs, err = images_agent.run(vp, rp, out, max_images=2)
    return imgs, err


@activity.defn
async def html_activity(output_dir: str, images: list[str], symbol_uri: str) -> str:
    """Generate portfolio HTML from template + images."""
    out = _out(output_dir)
    hp = out / "portfolio.html"
    rp, vp = out / "research.json", out / "vibe.json"
    if hp.exists():
        html = hp.read_text()
        if "data:image" in html:
            return html
    return html_agent.run(rp, vp, hp, images=images or None, symbol_img=symbol_uri or None)
