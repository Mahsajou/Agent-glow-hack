"""Contents agent — Exa get_contents. Output: contents.json"""

import json
from pathlib import Path

from agent.lib.exa_client import get_contents


def run(search_path: Path, output_path: Path) -> dict:
    search_data = json.loads(search_path.read_text())
    urls = search_data.get("urls", [])
    if not urls:
        data = {"urls": [], "contents": {}}
        output_path.write_text(json.dumps(data, indent=2))
        return data
    contents = get_contents(urls)
    data = {"urls": urls, "contents": contents}
    output_path.write_text(json.dumps(data, indent=2))
    return data
