"""Symbol agent — GMI image. Output: symbol.png"""

import base64
import json
from pathlib import Path

from agent.lib.gmi_client import GmiClient


def run(vibe_path: Path, research_path: Path, output_path: Path) -> str:
    vibe = json.loads(vibe_path.read_text())
    research = json.loads(research_path.read_text())
    summary = vibe.get("vibe_summary", "")
    personality = vibe.get("personality_match", "")
    accent = vibe.get("color_palette", {}).get("accent", "#6366f1")
    name = research.get("full_name", research.get("bio", "")[:30])
    prompt = (
        f"Minimal brand mark logo for {name}, {personality} aesthetic, {summary[:100]}. "
        f"Ancient mythology meets modern tech. Colors {accent} on dark. No text, no faces. Square, transparent background."
    )
    client = GmiClient()
    uri, err = client.generate_image(prompt, aspect_ratio="1:1")
    if not uri:
        return ""
    if output_path and uri.startswith("data:image/"):
        _, b64 = uri.split(",", 1)
        output_path.write_bytes(base64.b64decode(b64))
    return uri
