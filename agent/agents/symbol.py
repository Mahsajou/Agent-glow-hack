"""Symbol agent — GMI image. Output: symbol.png"""

import base64
from pathlib import Path

from agent.lib.gmi_client import GmiClient
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.symbol")


def run(vibe: dict, research: dict, output_path: Path) -> str:
    summary = vibe.get("vibe_summary", "")
    personality = vibe.get("personality_match", "")
    accent = vibe.get("color_palette", {}).get("accent", "#6366f1")
    name = research.get("full_name", research.get("bio", "")[:30])
    logger.info("symbol generating for name=%s", name[:40] if isinstance(name, str) else "")
    prompt = (
        f"Minimal brand mark logo for {name}, {personality} aesthetic, {summary[:100]}. "
        f"Ancient mythology meets modern tech. Colors {accent} on dark. No text, no faces. Square, transparent background."
    )
    client = GmiClient()
    uri, err = client.generate_image(prompt, aspect_ratio="1:1")
    if not uri:
        logger.warning("symbol generation failed err=%s", err)
        return ""
    logger.info("symbol done saved=%s", bool(output_path and uri.startswith("data:image/")))
    if output_path and uri.startswith("data:image/"):
        _, b64 = uri.split(",", 1)
        output_path.write_bytes(base64.b64decode(b64))
    return uri
