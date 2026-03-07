import json

from steps.gmi_client import get_gmi_client, GMI_FAST_MODEL

def infer_vibe(profile: dict) -> dict:
    prompt = f"""
You are a creative director and designer. Based on this person's professional profile,
infer the perfect visual aesthetic for their portfolio website.

PROFILE:
{json.dumps(profile, indent=2)}

Analyze signals like:
- Their domain (ML engineer vs designer vs founder vs researcher vs creative technologist)
- Their writing tone from bios, summaries, and writing samples
- Their personality notes and interests
- The type of work they do (systems vs product vs creative vs academic)
- Any explicit aesthetic preferences found in their online presence

Return a JSON object with EXACTLY these fields:
{{
  "vibe_summary": "2-3 sentence description of the design direction and why it fits this specific person",
  "theme": "dark",
  "typography_style": "e.g. editorial serif, technical mono, clean sans, expressive display",
  "color_palette": {{
    "background": "#hex",
    "surface": "#hex",
    "primary_text": "#hex",
    "secondary_text": "#hex",
    "accent": "#hex",
    "accent_secondary": "#hex"
  }},
  "layout_style": "e.g. brutalist grid, flowing editorial, dense technical, minimal whitespace, magazine",
  "motion_style": "e.g. subtle fades only, no animation, dramatic reveals, smooth parallax, typewriter effects",
  "personality_match": "e.g. precise and understated, bold and expressive, warm and approachable, raw and direct",
  "font_suggestions": {{
    "display": "exact Google Font name",
    "body": "exact Google Font name",
    "mono": "exact Google Font name"
  }},
  "tagline_style": "e.g. one punchy line, poetic fragment, technical descriptor, question"
}}

Be specific and committed to a clear aesthetic direction. 
Return ONLY valid JSON. No markdown fences, no explanation.
"""
    client = get_gmi_client()
    response = client.models.generate_content(
        model=GMI_FAST_MODEL,
        contents=[prompt]
    )
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        text = text[start:end]
    return json.loads(text)
