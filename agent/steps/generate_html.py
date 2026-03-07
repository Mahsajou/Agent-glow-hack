import json

from google.genai import types

from steps.gmi_client import get_gmi_client, GMI_MODEL

def generate_html(profile: dict, vibe: dict) -> str:
    fonts = vibe.get("font_suggestions", {})
    display_font = fonts.get("display", "Playfair Display")
    body_font = fonts.get("body", "Inter")
    mono_font = fonts.get("mono", "JetBrains Mono")
    colors = vibe.get("color_palette", {})

    prompt = f"""
You are a world-class frontend developer and designer. Generate a complete, single-file HTML portfolio.

DESIGN DIRECTION:
- Vibe: {vibe.get("vibe_summary", "")}
- Theme: {vibe.get("theme", "dark")}
- Typography style: {vibe.get("typography_style", "")}
- Layout: {vibe.get("layout_style", "")}
- Motion: {vibe.get("motion_style", "")}
- Personality: {vibe.get("personality_match", "")}
- Tagline style: {vibe.get("tagline_style", "")}
- Display font: {display_font}
- Body font: {body_font}
- Mono font: {mono_font}
- Colors: background={colors.get("background","#0a0a0a")}, surface={colors.get("surface","#111")}, 
  text={colors.get("primary_text","#f0f0f0")}, secondary={colors.get("secondary_text","#888")},
  accent={colors.get("accent","#ff6b35")}, accent2={colors.get("accent_secondary","#ff9f1c")}

PROFILE DATA:
{json.dumps(profile, indent=2)}

REQUIREMENTS:
- Single self-contained HTML file with ALL CSS and JS inline
- Import fonts from Google Fonts (use @import in <style>)
- Sections in order: Hero, About, Projects/Work, Skills, Contact
- Use ONLY information found in the profile — never invent details
- Mobile responsive with proper breakpoints
- Scroll-triggered reveal animations matching the motion_style
- Hover states on interactive elements
- The design must feel bespoke to THIS person — not a template
- Each section should have a distinct visual weight and rhythm
- Contact section should include links to their social/profiles if found in data
- Add a subtle footer with their name

Make it extraordinary. This is their professional face to the world.

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
