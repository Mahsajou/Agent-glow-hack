import json

from google.genai import types

from steps.gmi_client import get_gmi_client, GMI_MODEL

NUDGE_OPTIONS = [
    {"id": "hero",        "label": "Regenerate hero",           "icon": "Sparkles"},
    {"id": "projects",    "label": "Emphasize projects",        "icon": "FolderOpen"},
    {"id": "tone_warm",   "label": "Warmer tone",               "icon": "Sun"},
    {"id": "colors",      "label": "New color scheme",          "icon": "Palette"},
    {"id": "minimal",     "label": "More minimal",              "icon": "Minus"},
    {"id": "bold",        "label": "Bolder & more dramatic",    "icon": "Zap"},
    {"id": "skills",      "label": "Redesign skills section",   "icon": "Code"},
]

NUDGE_INSTRUCTIONS = {
    "hero": (
        "Rewrite ONLY the hero section. Make it more dramatic and memorable. "
        "The opening statement should be impossible to forget. Keep all other sections identical."
    ),
    "projects": (
        "Rewrite ONLY the projects/work section. Make each project more prominent — "
        "better visual hierarchy, more detail, stronger visual separation. Keep all other sections identical."
    ),
    "tone_warm": (
        "Rewrite the copy throughout the entire page to sound warmer and more human. "
        "Less corporate, more personal. Same structure and design, just friendlier words."
    ),
    "colors": (
        "Keep the exact layout and structure but apply a completely different color palette. "
        "It should still feel cohesive with the person's personality but be distinctly different visually."
    ),
    "minimal": (
        "Strip the design back significantly. Remove decorative elements, increase whitespace, "
        "let content breathe. Aim for restrained elegance. Keep all content."
    ),
    "bold": (
        "Make the design significantly more dramatic and bold. Larger typography, stronger contrasts, "
        "more visual tension. Keep all content but amplify the visual presence."
    ),
    "skills": (
        "Rewrite ONLY the skills section with a more creative, visually interesting presentation. "
        "Not just a list — make it feel alive. Keep all other sections identical."
    ),
}

def apply_nudge(nudge_id: str, current_html: str, profile: dict, vibe: dict) -> str:
    instruction = NUDGE_INSTRUCTIONS.get(nudge_id, "Improve the overall design quality.")
    prompt = f"""
You are a world-class frontend developer. You have an existing portfolio HTML file and need to apply a specific change.

CHANGE REQUESTED:
{instruction}

ORIGINAL VIBE DIRECTION:
{json.dumps(vibe, indent=2)}

PERSON'S PROFILE:
{json.dumps(profile, indent=2)}

CURRENT HTML:
{current_html}

Apply the requested change carefully. Return the complete updated HTML file.
Return ONLY valid HTML starting with <!DOCTYPE html>. No markdown, no explanation.
"""
    client = get_gmi_client()
    response = client.models.generate_content(
        model=GMI_MODEL,
        contents=[prompt],
        config=types.GenerateContentConfig(max_output_tokens=8192)
    )
    html = response.text.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return html
