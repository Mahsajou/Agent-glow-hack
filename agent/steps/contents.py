"""
Contents agent — fetch full web content for URLs from search.json.
Output: contents.json
"""

import json
import os
from pathlib import Path

from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])


def run_contents(search_path: Path, output_path: Path) -> dict:
    """
    Read URLs from search.json, fetch full contents, write contents.json.
    Returns the saved data.
    """
    search_data = json.loads(search_path.read_text())
    urls = search_data.get("urls", [])
    if not urls:
        data = {"urls": [], "contents": {}}
        output_path.write_text(json.dumps(data, indent=2))
        return data

    try:
        response = exa.get_contents(
            urls=urls,
            highlights={"max_characters": 4000},
        )
        contents = {
            r.url: {
                "text": r.text or "",
                "summary": r.summary or "",
                "highlights": r.highlights or [],
            }
            for r in response.results
        }
    except Exception as e:
        contents = {"error": str(e)}

    data = {
        "urls": urls,
        "contents": contents,
    }
    output_path.write_text(json.dumps(data, indent=2))
    return data
