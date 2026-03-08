"""
Infer Vibe agent — infer aesthetic from research.json.
Output: vibe.json
"""

import json
from pathlib import Path

from steps.gmi_client import get_gmi_client, GMI_LLM_MODEL


def run_infer_vibe(research_path: Path, output_path: Path) -> dict:
    """
    Read research.json, infer visual aesthetic via GMI, write vibe.json.
    Returns the saved data.
    """
    research = json.loads(research_path.read_text())
    if "error" in research:
        # Fallback vibe
        data = {
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
            "layout_style": "minimal clean",
            "motion_style": "subtle fades",
            "personality_match": "professional",
            "font_suggestions": {"display": "Inter", "body": "Inter", "mono": "JetBrains Mono"},
            "tagline_style": "one punchy line",
        }
        output_path.write_text(json.dumps(data, indent=2))
        return data

    prompt = f"""
You are a creative director and designer. Based on this person's research profile, infer the perfect visual aesthetic for their portfolio website.

RESEARCH:
{json.dumps(research, indent=2)}

Analyze: domain, writing tone, personality notes, interests, type of work.
Return a JSON object with EXACTLY these fields:
{{
  "vibe_summary": "2-3 sentence description of the design direction",
  "theme": "dark" or "light",
  "typography_style": "e.g. editorial serif, technical mono, clean sans",
  "color_palette": {{
    "background": "#hex",
    "surface": "#hex",
    "primary_text": "#hex",
    "secondary_text": "#hex",
    "accent": "#hex",
    "accent_secondary": "#hex"
  }},
  "layout_style": "e.g. brutalist grid, flowing editorial, minimal",
  "motion_style": "e.g. subtle fades, dramatic reveals",
  "personality_match": "e.g. precise and understated, bold and expressive",
  "font_suggestions": {{ "display": "Google Font name", "body": "...", "mono": "..." }},
  "tagline_style": "e.g. one punchy line, poetic fragment"
}}

Return ONLY valid JSON. No markdown fences, no explanation.
"""
    client = get_gmi_client()
    response = client.models.generate_content(
        model=GMI_LLM_MODEL,
        contents=[prompt],
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    data = json.loads(text)
    output_path.write_text(json.dumps(data, indent=2))
    return data
