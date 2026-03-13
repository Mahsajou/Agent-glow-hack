"""HTML agent — Generate template, inject images, validate, fix until valid.
Portfolio structure aligned with 12 aspects: identity, skills, projects, process,
impact, range, depth, credibility, journey, personality, communication, future."""

import json
import re
from pathlib import Path

from lxml import html as lxml_html

from agent.lib.openai_client import OpenAIClient, OPENAI_LLM_MODEL
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.html")

# Portfolio section spec — maps to the 12 aspects
SECTIONS_SPEC = """
REQUIRED SECTIONS (align with portfolio framework):

1. Hero — name, tagline, mission/identity (banner img)
2. About — identity, values, focus_areas, personal_philosophy, personality
3. Skills & Expertise — skills, tools_technologies, methodologies, domain_expertise
4. Key Projects — for each: name, description, outcome, impact_metrics, process_notes, url
5. Impact & Results — achievements, impact_statements (quantified)
6. Range & Depth — industries, project_types, specialization
7. Credibility — awards, publications, talks_presentations, certifications, testimonials
8. Journey — career_highlights, learning_milestones
9. Writing & Thinking — writing_samples, communication
10. Future Vision — future_vision, research_interests
11. Contact & Collaboration — social_links
12. Footer
"""

# Placeholders for image URLs (used in img src only — never inject HTML blocks)
PLACEHOLDER_BANNER = "{{BANNER_URL}}"
PLACEHOLDER_MOODBOARD = "{{MOODBOARD_URL}}"
PLACEHOLDER_SYMBOL = "{{SYMBOL_URL}}"

# 1x1 transparent PNG when no image is provided (keeps img valid)
EMPTY_IMG_DATA_URI = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

MAX_VALIDATE_ATTEMPTS = 3


def _normalize_projects(research: dict) -> list[dict]:
    """Ensure projects are structured. Fallback from notable_projects if needed."""
    projects = research.get("projects") or []
    if projects and isinstance(projects[0], dict):
        return projects
    fallback = research.get("notable_projects") or []
    return [
        {"name": p, "description": p, "outcome": "", "impact_metrics": [], "url": ""}
        for p in fallback
    ]


def _generate_template(client: OpenAIClient, research: dict, vibe: dict) -> str:
    """Step 1: Generate an HTML template with URL placeholders (not full HTML blocks)."""
    fonts = vibe.get("font_suggestions", {})
    colors = vibe.get("color_palette", {})
    display_font = fonts.get("display", "Inter")
    body_font = fonts.get("body", "Inter")
    mono_font = fonts.get("mono", "JetBrains Mono")
    layout_density = vibe.get("layout_density", "balanced")
    tone = vibe.get("tone", vibe.get("personality_match", "professional"))

    # Normalize projects for the prompt
    projects = _normalize_projects(research)
    research_for_prompt = {**research, "projects": projects}

    prompt = f"""You are a world-class frontend developer. Generate a complete, single-file HTML portfolio TEMPLATE.

PERSON'S BACKGROUND (use as content source — use projects array for structured project data):
{json.dumps(research_for_prompt, indent=2)}

{SECTIONS_SPEC}

DESIGN DIRECTION:
- Vibe: {vibe.get("vibe_summary", "")}
- Theme: {vibe.get("theme", "dark")}
- Typography: {vibe.get("typography_style", "")}, layout: {vibe.get("layout_style", "")}
- Layout density: {layout_density} — project-heavy = more project cards, story-heavy = more narrative
- Tone: {tone}
- Fonts: display={display_font}, body={body_font}, mono={mono_font}
- Colors: bg={colors.get("background","#0a0a0a")}, accent={colors.get("accent","#6366f1")}

CRITICAL - IMAGE PLACEHOLDERS (use ONLY inside img src attributes; they will be replaced with actual image URLs):
- {PLACEHOLDER_BANNER} — hero/banner image in HERO section: <img src="{PLACEHOLDER_BANNER}" alt="Hero banner" />
- {PLACEHOLDER_MOODBOARD} — moodboard image in ABOUT section: <img src="{PLACEHOLDER_MOODBOARD}" alt="Moodboard" />
- {PLACEHOLDER_SYMBOL} — brand symbol in NAV: <img src="{PLACEHOLDER_SYMBOL}" alt="Brand" class="brand-symbol" />

RULES:
- Put placeholders ONLY as the value of src= in img tags. Example: src="{PLACEHOLDER_BANNER}" NOT src="{{something}}"
- Include all sections that have data; omit empty ones
- For each project: show name, outcome, impact_metrics. Link to url when available
- Single self-contained HTML, inline CSS, Google Fonts @import
- Use ONLY info from the person's background — never invent
- Mobile responsive
Return ONLY valid HTML starting with <!DOCTYPE html>. No markdown, no explanation."""

    raw = client.generate_content(prompt, model=OPENAI_LLM_MODEL)
    out = raw.strip()
    if out.startswith("```"):
        out = out.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    idx = out.lower().find("<!doctype")
    if idx > 0:
        out = out[idx:]
    return out


def _inject_images(template: str, images: list | None, symbol_img: str | None) -> str:
    """Step 2: Inject image URLs into placeholders. Uses transparent pixel when no image."""
    banner_url = (images[0] if images and len(images) >= 1 else "") or EMPTY_IMG_DATA_URI
    moodboard_url = (images[1] if images and len(images) >= 2 else "") or EMPTY_IMG_DATA_URI
    symbol_url = symbol_img or EMPTY_IMG_DATA_URI

    html = template
    html = html.replace(PLACEHOLDER_BANNER, banner_url)
    html = html.replace(PLACEHOLDER_MOODBOARD, moodboard_url)
    html = html.replace(PLACEHOLDER_SYMBOL, symbol_url)
    return html


def _validate_html(html_content: str) -> tuple[bool, str]:
    """
    Step 3: Validate that the HTML is well-formed and properly formatted.
    Returns (is_valid, error_message).
    """
    # Check for invalid patterns (e.g. HTML/block content inside img src)
    bad_patterns = [
        (r'src\s*=\s*["\'][^"\']*<', "img src contains HTML or unescaped <"),
        (r'src\s*=\s*["\']\s*["\']', "empty img src"),
    ]
    for pat, msg in bad_patterns:
        if re.search(pat, html_content, re.IGNORECASE):
            return False, msg

    # Parse with lxml (lenient HTML parser)
    try:
        lxml_html.fromstring(html_content.encode("utf-8"))
        return True, ""
    except Exception as e:
        return False, f"Parse error: {e}"


def _fix_html(client: OpenAIClient, invalid_html: str, error: str) -> str:
    """Ask LLM to fix invalid HTML given the validation error."""
    prompt = f"""Fix this HTML. It failed validation with error: {error}

Rules:
- Image URLs (data:image/png;base64,...) must appear ONLY inside src="..." attributes of img tags.
- Never put div, figure, or other HTML elements inside an img src attribute.
- Return ONLY the corrected HTML. No markdown, no explanation.

HTML to fix:
{invalid_html[:15000]}
"""
    raw = client.generate_content(prompt, model=OPENAI_LLM_MODEL)
    out = raw.strip()
    if out.startswith("```"):
        out = out.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    idx = out.lower().find("<!doctype")
    if idx > 0:
        out = out[idx:]
    return out


def run(
    research: dict,
    vibe: dict,
    output_path: Path,
    images: list | None = None,
    symbol_img: str | None = None,
) -> str:
    """
    1. Generate template (placeholders in img src)
    2. Inject image URLs into placeholders
    3. Validate HTML
    4. Fix and repeat until valid
    """
    if research.get("error"):
        research = {"full_name": "Portfolio", "bio": "Error loading profile."}

    client = OpenAIClient()

    # Step 1: Generate template
    template = _generate_template(client, research, vibe)

    # Step 2: Inject image URLs
    html = _inject_images(template, images, symbol_img)

    # Steps 3–4: Validate and fix until valid
    for attempt in range(MAX_VALIDATE_ATTEMPTS):
        valid, error = _validate_html(html)
        if valid:
            break
        logger.warning("html validate attempt=%d error=%s", attempt + 1, error)
        if attempt < MAX_VALIDATE_ATTEMPTS - 1:
            html = _fix_html(client, html, error)

    logger.info("html done len=%d", len(html))
    output_path.write_text(html)
    return html
