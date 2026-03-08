"""
Generate a brand mark image from vibe.json and research.json via GMI image API.
Returns data URI string. Saves symbol.png.
"""

import base64
import json
from pathlib import Path

from steps.gmi_client import generate_image


def run_generate_symbol(
    vibe_path: Path, research_path: Path, output_path: Path | None = None
) -> str:
    """
    Read vibe.json and research.json, use GMI image API to generate a brand mark.
    Returns data URI or empty string on failure.
    """
    vibe = json.loads(vibe_path.read_text())
    research = json.loads(research_path.read_text())

    summary = vibe.get("vibe_summary", "")
    personality = vibe.get("personality_match", "")
    theme = vibe.get("theme", "dark")
    colors = vibe.get("color_palette", {})
    accent = colors.get("accent", "#6366f1")
    name = research.get("full_name", research.get("bio", "")[:30])

    prompt = (
        f"Minimal brand mark logo for {name}, "
        f"{personality} aesthetic, {summary[:100]}. "
        f"Ancient mythology meets modern tech: sacred geometry, mandala, circuit motifs. "
        f"Single cohesive symbol, colors {accent} on dark background. "
        f"No text, no faces. Clean, memorable, square aspect."
        f"The final symbol image generated must be strictly with transparent background."
    )

    uri, err = generate_image(prompt=prompt, aspect_ratio="1:1")
    if not uri:
        return ""

    if output_path:
        if uri.startswith("data:image/"):
            _, b64 = uri.split(",", 1)
            output_path.write_bytes(base64.b64decode(b64))

    return uri
