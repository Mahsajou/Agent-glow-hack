import os
from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])

def search_public_presence(name: str, context: str = "") -> list:
    queries = [
        f"{name} developer engineer portfolio projects",
        f"{name} {context} professional work".strip(),
        f'"{name}" blog writing talks interviews open source',
    ]
    all_results = []
    seen_urls = set()
    for query in queries:
        try:
            results = exa.search_and_contents(
                query,
                num_results=4,
                type="auto",
                contents={
                    "text": {"max_characters": 2000},
                    "summary": {"query": "professional background and personality"}
                }
            )
            for r in results.results:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    all_results.append({
                        "url": r.url,
                        "title": r.title or "",
                        "text": (r.text or "")[:800],
                        "summary": r.summary or "",
                    })
        except Exception:
            continue
    return all_results
