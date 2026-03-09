"""
Exa API client: Search, Contents, Research.
"""

import json
import os
import time
from typing import Any, Optional

from exa_py import Exa

RESEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string"},
        "current_role": {"type": "string"},
        "company": {"type": "string"},
        "bio": {"type": "string"},
        "skills": {"type": "array", "items": {"type": "string"}},
        "notable_projects": {"type": "array", "items": {"type": "string"}},
        "education": {"type": "string"},
        "social_links": {"type": "array", "items": {"type": "string"}},
        "achievements": {"type": "array", "items": {"type": "string"}},
        "writing_samples": {"type": "array", "items": {"type": "string"}},
        "interests_hobbies": {"type": "array", "items": {"type": "string"}},
        "personality_notes": {"type": "string"},
    },
    "required": ["full_name", "bio"],
    "additionalProperties": True,
}


def _get_exa():
    return Exa(api_key=os.environ["EXA_API_KEY"])


def search(query: str, num_results: int = 5, type_: str = "auto") -> list[dict]:
    """Search Exa. Returns list of {url, title}."""
    exa = _get_exa()
    results = exa.search(
        query,
        num_results=num_results,
        type=type_,
        contents={"highlights": {"max_characters": 4000}},
    )
    return [{"url": r.url, "title": r.title or ""} for r in results.results]


def get_contents(urls: list[str]) -> dict[str, dict]:
    """Fetch contents for URLs. Returns {url: {text, summary, highlights}}."""
    if not urls:
        return {}
    exa = _get_exa()
    try:
        response = exa.get_contents(urls=urls, highlights={"max_characters": 4000})
        return {
            r.url: {"text": r.text or "", "summary": r.summary or "", "highlights": r.highlights or []}
            for r in response.results
        }
    except Exception as e:
        return {"error": str(e)}


def research(instructions: str, model: str = "exa-research-fast") -> dict[str, Any]:
    """Exa Research: create task, poll until done. Returns parsed JSON or {error: str}."""
    exa = _get_exa()
    try:
        task = exa.research.create(
            instructions=instructions[:4096],
            model=model,
            output_schema=RESEARCH_OUTPUT_SCHEMA,
        )
    except Exception as e:
        return {"error": str(e)}

    research_id = getattr(task, "research_id", None) or getattr(task, "researchId", None)
    if not research_id:
        return {"error": "No researchId"}

    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            task = exa.research.get(research_id, stream=False)
        except Exception as e:
            return {"error": f"Poll failed: {e}"}
        status = getattr(task, "status", "")
        if status == "completed":
            output = getattr(task, "output", None)
            if not output:
                return {"error": "No output"}
            parsed = getattr(output, "parsed", None)
            content = getattr(output, "content", None)
            if parsed is not None:
                return parsed if isinstance(parsed, dict) else json.loads(parsed)
            if content:
                return json.loads(content) if isinstance(content, str) else content
            return {"error": "No parsed/content"}
        if status in ("failed", "canceled", "cancelled"):
            return {"error": str(getattr(task, "error", "Research failed"))}
        time.sleep(2)
    return {"error": "Research timed out"}
