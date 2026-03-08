"""
Generate 1–2 AI images matching the user's vibe for the portfolio.
Uses GMI gemini-3.1-flash-image-preview. Returns list of base64 data URIs.
"""

from typing import Optional

from steps.gmi_client import generate_image


def generate_portfolio_images(
    vibe: dict,
    profile_name: str,
    max_images: int = 2,
) -> list[str]:
    """
    Generate decorative images for the portfolio based on vibe and profile.
    Returns list of data URIs (data:image/png;base64,...), empty on failure.
    """
    colors = vibe.get("color_palette", {})
    accent = colors.get("accent", "#6366f1")
    personality = vibe.get("personality_match", "professional")
    vibe_summary = vibe.get("vibe_summary", "")
    layout = vibe.get("layout_style", "minimal")

    prompts = []

    # 1. Banner for the user — hero/header image
    banner_prompt = (
        f"Wide hero banner image for a professional portfolio website, "
        f"{personality} aesthetic, {vibe_summary[:150]}. "
        f"Use color palette with {accent} and complementary tones. "
        f"Atmospheric, evocative background — could be abstract gradients, "
        f"subtle geometric patterns, or a moody ambient scene. "
        f"No text, no faces, no logos. Clean and sophisticated, "
        f"suitable as a full-width header banner."
    )
    prompts.append(banner_prompt)

    # 2. Moodboard based on user's vibe
    if max_images >= 2:
        moodboard_prompt = (
            f"Creative moodboard collage representing this aesthetic: "
            f"{vibe_summary}. "
            f"Personality: {personality}. Layout style: {layout}. "
            f"Colors: {accent} and palette. "
            f"Combine textures, shapes, and visual motifs that evoke this vibe — "
            f"could include abstract forms, gradients, typography hints, "
            f"minimal line art, or pattern fragments. "
            f"Cohesive collage composition, no readable text. "
            f"Professional moodboard suitable for a portfolio about section."
        )
        prompts.append(moodboard_prompt)

    images: list[str] = []
    for prompt in prompts[:max_images]:
        uri: Optional[str] = generate_image(
            prompt=prompt,
            aspect_ratio="16:9",
            resolution="1K",
        )
        if uri:
            images.append(uri)
    return images
