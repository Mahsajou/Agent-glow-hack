"""
Generate portfolio HTML from research.json, vibe.json, images, and symbol.
Template-based: loads template, fills from JSON, injects images.
"""

import html
import json
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "portfolio.html"


def _fmt_list(items: list, tag: str = "li") -> str:
    if not items:
        return ""
    return "".join(f"<{tag}>{html.escape(str(x))}</{tag}>" for x in items)


def _link_list(links: list) -> str:
    if not links:
        return ""
    out = []
    for url in links:
        url = str(url).strip()
        if not url.startswith("http"):
            url = "https://" + url
        label = url.replace("https://", "").replace("http://", "").split("/")[0]
        if "linkedin" in label.lower():
            label = "LinkedIn"
        elif "github" in label.lower():
            label = "GitHub"
        elif "twitter" in label.lower() or "x.com" in label.lower():
            label = "Twitter"
        elif "instagram" in label.lower():
            label = "Instagram"
        elif "youtube" in label.lower():
            label = "YouTube"
        out.append(f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>')
    return " · ".join(out)


def run_generate_html(
    research_path: Path,
    vibe_path: Path,
    images: list[str] | None = None,
    symbol_img: str | None = None,
) -> str:
    """
    Build portfolio HTML from template + research + vibe JSON. Images injected at fixed positions.
    """
    research = json.loads(research_path.read_text())
    vibe = json.loads(vibe_path.read_text())

    if research.get("error"):
        research = {"full_name": "Portfolio", "bio": "Error loading profile."}

    fonts = vibe.get("font_suggestions", {})
    colors = vibe.get("color_palette", {})
    display_font = fonts.get("display", "Inter").replace(" ", "+")
    body_font = fonts.get("body", "Inter").replace(" ", "+")
    mono_font = fonts.get("mono", "JetBrains Mono").replace(" ", "+")
    bg = colors.get("background", "#0a0a0a")
    surface = colors.get("surface", "#111")
    accent = colors.get("accent", "#6366f1")
    text_primary = colors.get("primary_text", "#f0f0f0")
    text_secondary = colors.get("secondary_text", "#888")

    name = html.escape(research.get("full_name", ""))
    role = html.escape(research.get("current_role", ""))
    company = html.escape(research.get("company", ""))
    bio = html.escape(research.get("bio", ""))
    tagline = (research.get("writing_samples") or [""])[0] or bio[:120]
    tagline = html.escape(str(tagline)[:150])
    brand_name = name.split()[0] if name else "Portfolio"

    role_display = role + (" at " + company if company else "")
    skills = research.get("skills", [])[:12]
    projects = research.get("notable_projects", [])[:6]
    social_links = research.get("social_links", [])
    education = research.get("education", "")
    education_html = f'<p style="margin-top:1rem;color:var(--text-muted);">{html.escape(education)}</p>' if education else ""

    banner_html = ""
    if images and len(images) >= 1:
        banner_html = f'<div class="hero-banner"><img src="{images[0]}" alt="Hero banner" /></div>'

    moodboard_html = ""
    if images and len(images) >= 2:
        moodboard_html = f'<figure class="about-visual"><img src="{images[1]}" alt="Moodboard" /></figure>'

    symbol_html = ""
    if symbol_img:
        symbol_html = f'<img src="{symbol_img}" alt="Brand" class="brand-symbol" />'

    projects_html = _fmt_list(projects) if projects else "<li>No projects listed.</li>"
    skills_html = _fmt_list(skills, "span") if skills else "<span>—</span>"
    contact_html = _link_list(social_links) if social_links else "<span>—</span>"

    template = TEMPLATE_PATH.read_text()
    return template.format(
        name=name,
        role=role_display,
        tagline=tagline,
        bio=bio,
        brand_name=brand_name,
        display_font=display_font,
        body_font=body_font,
        mono_font=mono_font,
        bg=bg,
        surface=surface,
        accent=accent,
        text_primary=text_primary,
        text_secondary=text_secondary,
        banner_html=banner_html,
        moodboard_html=moodboard_html,
        symbol_html=symbol_html,
        education_html=education_html,
        projects_html=projects_html,
        skills_html=skills_html,
        contact_html=contact_html,
    )
