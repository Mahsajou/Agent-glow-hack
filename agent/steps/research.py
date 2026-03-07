import os
from exa_py import Exa

exa = Exa(api_key=os.environ["EXA_API_KEY"])

SCHEMA = {
    "type": "object",
    "properties": {
        "full_name":         {"type": "string"},
        "current_role":      {"type": "string"},
        "company":           {"type": "string"},
        "bio":               {"type": "string"},
        "skills":            {"type": "array", "items": {"type": "string"}},
        "notable_projects":  {"type": "array", "items": {"type": "string"}},
        "education":         {"type": "string"},
        "social_links":      {"type": "array", "items": {"type": "string"}},
        "achievements":      {"type": "array", "items": {"type": "string"}},
        "writing_samples":   {"type": "array", "items": {"type": "string"}},
        "interests_hobbies": {"type": "array", "items": {"type": "string"}},
        "personality_notes": {"type": "string"}
    }
}

def research_person(name: str, context: str = "", timeout: int = 90) -> dict:
    try:
        task = exa.research.create(
            instructions=(
                f"Research the professional and personal background of {name}. {context}. "
                f"Find their current role, skills, notable projects, education, and achievements. "
                f"Also capture any writing samples or quotes, side interests or hobbies, "
                f"and personality signals — are they technical and precise? creative and expressive? "
                f"minimalist? verbose? playful? serious? What is their communication style?"
            ),
            output_schema=SCHEMA
        )

        result = exa.research.poll_until_finished(
            task.research_id,
            poll_interval=4000,
            timeout_ms=timeout * 1000,
        )

        if result.status == "completed":
            if result.output and result.output.parsed:
                return result.output.parsed
            elif result.output and result.output.content:
                import json
                try:
                    return json.loads(result.output.content)
                except json.JSONDecodeError:
                    return {"error": "Could not parse research output", "raw": result.output.content[:500]}
            return {}
        elif result.status == "failed":
            return {"error": f"Research task failed: {getattr(result, 'error', 'unknown')}"}
        else:
            return {"error": f"Research ended with status: {result.status}"}
    except Exception as e:
        return {"error": str(e)}
