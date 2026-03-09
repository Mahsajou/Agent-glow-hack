"""Infer Vibe agent — GMI LLM. Output: vibe.json"""

import json
from pathlib import Path

from agent.lib.gmi_client import GmiClient, GMI_LLM_MODEL

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
    "motion_style": "subtle fades",
    "personality_match": "professional",
    "font_suggestions": {"display": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
    "tagline_style": "one punchy line",
}


def run(research_path: Path, output_path: Path) -> dict:
    research = json.loads(research_path.read_text())
    if research.get("error"):
        output_path.write_text(json.dumps(FALLBACK_VIBE, indent=2))
        return FALLBACK_VIBE
    prompt = f"""You are a creative director. Based on this profile, infer the perfect visual aesthetic.

RESEARCH:
{json.dumps(research, indent=2)}

Return a JSON object with: vibe_summary, theme, typography_style, color_palette (background, surface, primary_text, secondary_text, accent, accent_secondary), layout_style, motion_style, personality_match, font_suggestions (display, body, mono), tagline_style.
Return ONLY valid JSON. No markdown."""
    client = GmiClient()
    text = client.generate_content(prompt, model=GMI_LLM_MODEL)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    i, j = text.find("{"), text.rfind("}") + 1
    if i >= 0 and j > i:
        text = text[i:j]
    data = json.loads(text)
    output_path.write_text(json.dumps(data, indent=2))
    return data
