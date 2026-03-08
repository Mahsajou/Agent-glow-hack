import json

from steps.gmi_client import get_gmi_client, GMI_FAST_MODEL


def generate_html(profile: dict, vibe: dict, images: list[str] | None = None) -> str:
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
- Do NOT include any profile photo or image in the hero — names can be ambiguous and photos may not represent the correct person
- Use ONLY information found in the profile — never invent details
- Mobile responsive with proper breakpoints
- Scroll-triggered reveal animations matching the motion_style
- Hover states on interactive elements
- The design must feel bespoke to THIS person — not a template
- Each section should have a distinct visual weight and rhythm
- Contact section should include links to their social/profiles if found in data
- Add a subtle footer with their name

DECORATIVE ART (keep neat and minimal):
- Add 1–2 subtle inline SVG or CSS decorative elements that match the vibe and color palette:
  e.g. a soft gradient blob, geometric accent, or abstract shape in the hero or between sections
- Use the accent colors sparingly — these should enhance, not clutter
- Ensure decorative elements feel cohesive with the personality_match (e.g. precise → clean geometry; expressive → organic shapes; minimal → restrained gradients)
- Position them so they frame content without competing with it
- Keep the page clean and professional — the art should elevate, not distract
"""
    if images:
        prompt += f"""
AI-GENERATED IMAGES TO EMBED:
You have {len(images)} AI-generated image(s) to include:
- Image 1 (BANNER): Use as the hero/header banner — full-width background or prominent banner image at the top. Use width 100%, object-fit: cover, optional subtle overlay for text readability.
- Image 2 (MOODBOARD, if provided): Place in the About section as a moodboard that captures the person's aesthetic. Size it tastefully (e.g. max-width 400–500px or 50% width), border-radius 8px, let it complement the copy.
Embed each as <img src="..." alt="" /> with the exact data URI provided. Keep the layout clean and aesthetic.
IMAGE 1 DATA URI:
{images[0]}
"""
        if len(images) >= 2:
            prompt += f"""
IMAGE 2 DATA URI:
{images[1]}
"""
        prompt += "\n"
    prompt += """
Make it extraordinary. This is their professional face to the world.

Return ONLY valid HTML starting with <!DOCTYPE html>. No markdown, no explanation.
"""
    client = get_gmi_client()
    response = client.models.generate_content(
        model=GMI_FAST_MODEL,
        contents=[prompt],
        config=None
    )
    html = response.text.strip()
    if html.startswith("```"):
        html = html.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    doctype_idx = html.lower().find("<!doctype")
    if doctype_idx > 0:
        html = html[doctype_idx:]
    return html
