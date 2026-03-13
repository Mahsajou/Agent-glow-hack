"""
Exa API client: Search, Contents, Research.
"""

import json
import os
import time
from typing import Any, Optional

from exa_py import Exa

# Portfolio framework schema: 12 aspects (identity, skills, projects, process, impact,
# range, depth, credibility, journey, personality, communication, future)
RESEARCH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        # 1. Identity
        "full_name": {"type": "string"},
        "current_role": {"type": "string"},
        "company": {"type": "string"},
        "bio": {"type": "string"},
        "mission_statement": {"type": "string"},
        "focus_areas": {"type": "array", "items": {"type": "string"}},
        "values": {"type": "array", "items": {"type": "string"}},
        # 2. Skills
        "skills": {"type": "array", "items": {"type": "string"}},
        "tools_technologies": {"type": "array", "items": {"type": "string"}},
        "methodologies": {"type": "array", "items": {"type": "string"}},
        "domain_expertise": {"type": "array", "items": {"type": "string"}},
        # 3. Projects (structured) + 4. Process, 5. Impact
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "outcome": {"type": "string"},
                    "impact_metrics": {"type": "array", "items": {"type": "string"}},
                    "process_notes": {"type": "string"},
                    "url": {"type": "string"},
                    "role": {"type": "string"},
                },
            },
        },
        "notable_projects": {"type": "array", "items": {"type": "string"}},
        "achievements": {"type": "array", "items": {"type": "string"}},
        "impact_statements": {"type": "array", "items": {"type": "string"}},
        # 6. Range, 7. Depth, 8. Credibility
        "industries": {"type": "array", "items": {"type": "string"}},
        "project_types": {"type": "array", "items": {"type": "string"}},
        "specialization": {"type": "string"},
        "awards": {"type": "array", "items": {"type": "string"}},
        "publications": {"type": "array", "items": {"type": "string"}},
        "talks_presentations": {"type": "array", "items": {"type": "string"}},
        "certifications": {"type": "array", "items": {"type": "string"}},
        "testimonials": {"type": "array", "items": {"type": "string"}},
        "media_coverage": {"type": "array", "items": {"type": "string"}},
        "education": {"type": "string"},
        "social_links": {"type": "array", "items": {"type": "string"}},
        # 9. Journey
        "career_highlights": {"type": "array", "items": {"type": "string"}},
        "learning_milestones": {"type": "array", "items": {"type": "string"}},
        # 10. Personality, 11. Communication, 12. Future
        "writing_samples": {"type": "array", "items": {"type": "string"}},
        "interests_hobbies": {"type": "array", "items": {"type": "string"}},
        "personality_notes": {"type": "string"},
        "personal_philosophy": {"type": "string"},
        "future_vision": {"type": "string"},
        "research_interests": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["full_name", "bio"],
    "additionalProperties": True,
}


def _get_exa():
    return Exa(api_key=os.environ["EXA_API_KEY"])


def _with_retries(func, max_retries: int = 3, base_delay: float = 1.0, label: str = ""):
    """Simple retry helper for transient Exa errors (including rate limiting)."""
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:  # noqa: BLE001
            last_err = e
            # Backoff before next attempt, except after last
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                time.sleep(delay)
            continue
    # Exhausted retries
    raise last_err  # type: ignore[misc]


def search(query: str, num_results: int = 5, type_: str = "auto") -> list[dict]:
    """Search Exa. Returns list of {url, title}."""
    exa = _get_exa()
    results = _with_retries(
        lambda: exa.search(
            query,
            num_results=num_results,
            type=type_,
            contents={"highlights": {"max_characters": 4000}},
        ),
        max_retries=3,
        base_delay=1.0,
        label="search",
    )
    return [{"url": r.url, "title": r.title or ""} for r in results.results]


def get_contents(urls: list[str]) -> dict[str, dict]:
    """Fetch contents for URLs. Returns {url: {text, summary, highlights}}."""
    if not urls:
        return {}
    exa = _get_exa()
    try:
        response = _with_retries(
            lambda: exa.get_contents(urls=urls, highlights={"max_characters": 4000}),
            max_retries=3,
            base_delay=1.0,
            label="contents",
        )
        return {
            r.url: {"text": r.text or "", "summary": r.summary or "", "highlights": r.highlights or []}
            for r in response.results
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def research(instructions: str, model: str = "exa-research-fast") -> dict[str, Any]:
    """Exa Research: create task, poll until done. Returns parsed JSON or {error: str}."""
    exa = _get_exa()
    try:
        task = _with_retries(
            lambda: exa.research.create(
                instructions=instructions[:4096],
                model=model,
                output_schema=RESEARCH_OUTPUT_SCHEMA,
            ),
            max_retries=3,
            base_delay=2.0,
            label="research.create",
        )
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}

    research_id = getattr(task, "research_id", None) or getattr(task, "researchId", None)
    if not research_id:
        return {"error": "No researchId"}

    deadline = time.time() + 180
    while time.time() < deadline:
        try:
            task = _with_retries(
                lambda: exa.research.get(research_id, stream=False),
                max_retries=3,
                base_delay=1.0,
                label="research.get",
            )
        except Exception as e:  # noqa: BLE001
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
