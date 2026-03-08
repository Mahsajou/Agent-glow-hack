"""
Generate banner and moodboard images from vibe.json + research.json.
Returns (list of data URIs, error_message or None).
"""

from typing import Optional

from steps.gmi_client import generate_image


def run_generate_images(
    vibe_path,
    research_path,
    max_images: int = 2,
) -> tuple[list[str], Optional[str]]:
    """
    Read vibe.json and research.json, generate banner + moodboard.
    Returns (list of data URIs, error_message or None).
    """
    import json

    try:
        vibe = json.loads(vibe_path.read_text())
    except Exception as e:
        return [], str(e)
    try:
        research = json.loads(research_path.read_text())
    except Exception as e:
        return [], str(e)

    colors = vibe.get("color_palette", {})
    accent = colors.get("accent", "#6366f1")
    personality = vibe.get("personality_match", "professional")
    vibe_summary = vibe.get("vibe_summary", "")
    layout = vibe.get("layout_style", "minimal")

    bio = research.get("bio", "")

    prompts = []
    banner_prompt = (
        f"Wide hero banner for portfolio, "
        f"{personality} aesthetic, {vibe_summary[:120]}. "
        f"Colors: {accent}. Atmospheric background, abstract gradients or patterns. "
        f"No text, no faces, no logos. Clean and sophisticated."
    )
    prompts.append(banner_prompt)

    if max_images >= 2:
        moodboard_prompt = (
            f"Creative moodboard with vibe: {vibe_summary}. "
            f"Personality: {personality}. Layout: {layout}. "
            f"Colors: {accent}. Textures, shapes, visual motifs. "
            f"Cohesive collage, no readable text. Professional."
        )
        prompts.append(moodboard_prompt)

    images = []
    last_err = None
    for p in prompts[:max_images]:
        uri, err = generate_image(prompt=p, aspect_ratio="16:9")
        if uri:
            images.append(uri)
        else:
            last_err = err or "Image generation returned no data"
    return images, last_err if not images else None
