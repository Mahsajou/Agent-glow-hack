"""Temporal activities for nudge (patch HTML)."""

import json
from pathlib import Path

from temporalio import activity

from agent.agents import nudge as nudge_agent
from agent.agents.nudge import NUDGE_OPTIONS


@activity.defn
async def nudge_activity(nudge_id: str, output_dir: str) -> str:
    out = Path(output_dir)
    research = json.loads((out / "research.json").read_text())
    vibe = json.loads((out / "vibe.json").read_text())
    html = (out / "portfolio.html").read_text()
    new_html = nudge_agent.run(nudge_id, html, research, vibe)
    (out / "portfolio.html").write_text(new_html)
    return new_html


@activity.defn
async def nudge_options_activity() -> list[dict]:
    return NUDGE_OPTIONS
