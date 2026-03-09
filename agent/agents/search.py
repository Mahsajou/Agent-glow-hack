"""Search agent — Exa Search. Output: search.json"""

import json
from pathlib import Path

from agent.lib.exa_client import search as exa_search


def run(name: str, context: str, output_path: Path) -> dict:
    queries = [
        f"{name} developer engineer portfolio projects",
        f"{name} {context} professional work".strip() or f"{name} professional",
        f'"{name}" blog writing talks interviews open source',
    ]
    all_results = []
    seen = set()
    for q in queries:
        try:
            for r in exa_search(q, num_results=5):
                if r["url"] not in seen:
                    seen.add(r["url"])
                    all_results.append(r)
        except Exception:
            continue
    data = {"name": name, "context": context, "urls": [r["url"] for r in all_results], "results": all_results}
    output_path.write_text(json.dumps(data, indent=2))
    return data
