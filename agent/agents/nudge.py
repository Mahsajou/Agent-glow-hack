"""Nudge agent — GMI LLM to patch HTML."""

import json

from agent.lib.gmi_client import GmiClient, GMI_LLM_MODEL
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.nudge")

NUDGE_OPTIONS = [
    {"id": "hero", "label": "Regenerate hero", "icon": "Sparkles"},
    {"id": "projects", "label": "Emphasize projects", "icon": "FolderOpen"},
    {"id": "tone_warm", "label": "Warmer tone", "icon": "Sun"},
    {"id": "colors", "label": "New color scheme", "icon": "Palette"},
    {"id": "minimal", "label": "More minimal", "icon": "Minus"},
    {"id": "bold", "label": "Bolder & dramatic", "icon": "Zap"},
    {"id": "skills", "label": "Redesign skills", "icon": "Code"},
]

INSTRUCTIONS = {
    "hero": "Rewrite ONLY the hero. More dramatic and memorable. Keep rest identical.",
    "projects": "Rewrite ONLY projects section. Better hierarchy. Keep rest identical.",
    "tone_warm": "Rewrite copy to sound warmer, friendlier. Same structure.",
    "colors": "Apply a different color palette. Same layout.",
    "minimal": "Strip back design. More whitespace. Keep content.",
    "bold": "More dramatic: larger type, stronger contrast.",
    "skills": "Rewrite skills section creatively. Keep rest identical.",
}


def run(nudge_id: str, html: str, research: dict, vibe: dict) -> str:
    instruction = INSTRUCTIONS.get(nudge_id, "Improve design quality.")
    prompt = f"""Apply this change to the HTML:
{instruction}

VIBE: {json.dumps(vibe, indent=2)}
RESEARCH: {json.dumps(research, indent=2)}

CURRENT HTML:
{html}

Return the complete updated HTML. Only valid HTML, no markdown."""
    client = GmiClient()
    out = client.generate_content(prompt, model=GMI_LLM_MODEL)
    out = out.strip()
    if out.startswith("```"):
        out = out.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    i = out.lower().find("<!doctype")
    if i > 0:
        out = out[i:]
    logger.info("nudge done len=%d", len(out))
    return out
