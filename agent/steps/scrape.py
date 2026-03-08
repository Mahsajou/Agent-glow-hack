import os
from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])

def scrape_links(urls: list[str]) -> dict:
    try:
        response = exa.get_contents(
            ids=urls,
            text={"max_characters": 5000},
            highlights={"num_sentences": 5, "highlights_per_url": 3},
            summary={"query": "professional background, skills, projects, personality, writing style, values"}
        )
        return {
            r.url: {
                "text": r.text or "",
                "summary": r.summary or "",
                "highlights": r.highlights or [],
            }
            for r in response.results
        }
    except Exception as e:
        return {"error": str(e)}
