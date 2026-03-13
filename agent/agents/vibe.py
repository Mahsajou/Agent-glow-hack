"""Infer Vibe agent — OpenAI LLM. Output: vibe.json.
Infers visual aesthetic and content structure (layout_density, tone) from research."""

import json
from pathlib import Path

from agent.lib.openai_client import OpenAIClient, OPENAI_LLM_MODEL
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.vibe")

FALLBACK_VIBE = {
    "vibe_summary": "Clean, professional dark portfolio",
    "theme": "dark",
    "typography_style": "clean sans",
    "color_palette": {
        "background": "#0a0a0a",
        "surface": "#111",
        "primary_text": "#f0f0f0",
        "secondary_text": "#888",
        "accent": "#6366f1",
        "accent_secondary": "#8b5cf6",
    },
    "layout_style": "minimal",
    "layout_density": "balanced",
    "tone": "professional",
    "motion_style": "subtle fades",
    "personality_match": "professional",
    "font_suggestions": {"display": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
    "tagline_style": "one punchy line",
}

VIBE_JSON_SPEC = """Return a JSON object with:
- vibe_summary: short description of the aesthetic
- theme: dark | light
- typography_style: e.g. clean sans, editorial serif, tech mono
- color_palette: {background, surface, primary_text, secondary_text, accent, accent_secondary}
- layout_style: minimal | editorial | bold | structured
- layout_density: project-heavy (many project cards) | story-heavy (more narrative) | balanced
- tone: formal | academic | creative | expressive | technical | minimal
- motion_style: subtle fades | none | bold
- personality_match: professional | creative | technical | artistic
- font_suggestions: {display, body, mono}
- tagline_style: one punchy line | descriptive | minimal
Return ONLY valid JSON. No markdown."""


def run(research: dict, output_path: Path) -> dict:
    if research.get("error"):
        output_path.write_text(json.dumps(FALLBACK_VIBE, indent=2))
        return FALLBACK_VIBE
    prompt = f"""You are a creative director. Based on this profile, infer the perfect visual aesthetic.

Consider content structure:
- If many projects (projects/notable_projects): layout_density = "project-heavy"
- If narrative-focused (writing_samples, personal_philosophy): layout_density = "story-heavy"
- specialization, domain_expertise → tone (technical vs creative)
- personality_notes, interests → tone (expressive vs minimal)

RESEARCH:
{json.dumps(research, indent=2)}

{VIBE_JSON_SPEC}"""
    client = OpenAIClient()
    text = client.generate_content(prompt, model=OPENAI_LLM_MODEL)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    i, j = text.find("{"), text.rfind("}") + 1
    if i >= 0 and j > i:
        text = text[i:j]
    data = json.loads(text)
    # Ensure new fields have defaults for HTML agent
    data.setdefault("layout_density", FALLBACK_VIBE["layout_density"])
    data.setdefault("tone", data.get("personality_match", FALLBACK_VIBE["tone"]))
    logger.info("vibe done theme=%s layout_density=%s", data.get("theme", "unknown"), data.get("layout_density"))
    output_path.write_text(json.dumps(data, indent=2))
    return data
