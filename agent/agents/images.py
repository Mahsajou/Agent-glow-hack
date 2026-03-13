"""Images agent — GMI image. Output: banner.png, moodboard.png"""

import base64
from pathlib import Path
from typing import Optional

from agent.lib.gmi_client import GmiClient
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.images")


def run(vibe: dict, research: dict, output_dir: Path, max_images: int = 2) -> tuple[list[str], Optional[str]]:
    c = vibe.get("color_palette", {})
    accent = c.get("accent", "#6366f1")
    personality = vibe.get("personality_match", "professional")
    summary = vibe.get("vibe_summary", "")
    layout = vibe.get("layout_style", "minimal")
    prompts = [
        f"Wide hero banner, {personality} aesthetic, {summary[:120]}. Colors {accent}. Atmospheric, no text, no faces.",
        f"Creative moodboard: {summary}. {personality}. {layout}. Colors {accent}. Textures, shapes. No readable text.",
    ]
    client = GmiClient()
    images = []
    last_err = None
    for p in prompts[:max_images]:
        uri, err = client.generate_image(p, aspect_ratio="16:9")
        if uri:
            images.append(uri)
            if uri.startswith("data:image/"):
                _, b64 = uri.split(",", 1)
                out = output_dir / ("banner.png" if len(images) == 1 else "moodboard.png")
                out.write_bytes(base64.b64decode(b64))
        else:
            logger.warning("images prompt failed err=%s", err)
            last_err = err
    logger.info("images done count=%d err=%s", len(images), last_err)
    return images, last_err if not images else None
