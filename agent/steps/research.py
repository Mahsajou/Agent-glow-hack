"""
Deep Research agent — explore the web and synthesize professional background via Exa Research SDK.
Uses exa.research.create() and exa.research.get() for polling.
Output: research.json with structured profile.
"""

import json
import os
import time
from pathlib import Path

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


def run_research(name: str, context: str, output_path: Path, model: str = "exa-research-fast") -> dict:
    """
    Use Exa Research SDK to explore the web and return structured profile.
    Creates task, polls get() until completed.
    """
    api_key = os.environ.get("EXA_API_KEY")
    if not api_key:
        data = {"error": "EXA_API_KEY not set"}
        output_path.write_text(json.dumps(data, indent=2))
        return data

    exa = Exa(api_key=api_key)

    instructions = f"""Research {name} professionally and personally.

Find and extract: full name, current role, company, bio (2-4 sentences), skills (technologies, tools, languages), notable projects with brief descriptions, education, social links (LinkedIn, GitHub, personal site, Twitter, etc.), achievements, representative writing samples or quotes, interests/hobbies, and personality/aesthetic notes (communication style, tone).

{f'Context: {context}' if context else ''}

Use ONLY information found from web sources. Never invent details. Be thorough but concise."""

    try:
        research = exa.research.create(
            instructions=instructions[:4096],
            model=model,
            output_schema=RESEARCH_OUTPUT_SCHEMA,
        )
    except Exception as e:
        data = {"error": str(e)}
        output_path.write_text(json.dumps(data, indent=2))
        return data

    research_id = getattr(research, "research_id", None) or getattr(research, "researchId", None)
    if not research_id:
        data = {"error": "No researchId in create response"}
        output_path.write_text(json.dumps(data, indent=2))
        return data

    # Poll until completed (max ~3 min)
    deadline = time.time() + 180
    poll_interval = 2

    while time.time() < deadline:
        try:
            task = exa.research.get(research_id, stream=False)
        except Exception as e:
            data = {"error": f"Poll failed: {e}"}
            output_path.write_text(json.dumps(data, indent=2))
            return data

        status = getattr(task, "status", "")

        if status == "completed":
            output = getattr(task, "output", None)
            if not output:
                data = {"error": "Completed but no output"}
                output_path.write_text(json.dumps(data, indent=2))
                return data
            parsed = getattr(output, "parsed", None)
            content = getattr(output, "content", None)
            if parsed is not None:
                data = parsed
                if isinstance(data, str):
                    data = json.loads(data)
            elif content:
                data = json.loads(content) if isinstance(content, str) else content
            else:
                data = {"error": "No parsed or content in output"}
            output_path.write_text(json.dumps(data, indent=2))
            return data

        if status in ("failed", "canceled", "cancelled"):
            err = getattr(task, "error", "Research failed")
            data = {"error": str(err)}
            output_path.write_text(json.dumps(data, indent=2))
            return data

        time.sleep(poll_interval)

    data = {"error": "Research timed out after 3 minutes"}
    output_path.write_text(json.dumps(data, indent=2))
    return data
