"""
Search agent — find URLs and basic info about the person via Exa Search.
Output: search.json
"""

import json
import os
from pathlib import Path

from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])


def run_search(name: str, context: str, output_path: Path) -> dict:
    """
    Search for the person's public presence. Writes search.json.
    Returns the saved data for use in run.py.
    """
    queries = [
        f"{name} developer engineer portfolio projects",
        f"{name} {context} professional work".strip() or f"{name} professional",
        f'"{name}" blog writing talks interviews open source',
    ]
    all_results = []
    seen_urls = set()
    for query in queries:
        try:
            results = exa.search(
                query,
                num_results=5,
                type="auto",
                contents={
                    "highlights": {"max_characters": 4000},
                },
            )
            for r in results.results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append({
                        "url": r.url,
                        "title": r.title or "",
                    })
        except Exception:
            continue

    data = {
        "name": name,
        "context": context,
        "urls": [r["url"] for r in all_results],
        "results": all_results,
    }
    output_path.write_text(json.dumps(data, indent=2))
    return data
