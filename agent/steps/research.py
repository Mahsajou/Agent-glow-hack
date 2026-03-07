import os
import time
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

def research_person(name: str, context: str = "", timeout: int = 60) -> dict:
    try:
        task = exa.research.create_task(
            instructions=(
                f"Research the professional and personal background of {name}. {context}. "
                f"Find their current role, skills, notable projects, education, and achievements. "
                f"Also capture any writing samples or quotes, side interests or hobbies, "
                f"and personality signals — are they technical and precise? creative and expressive? "
                f"minimalist? verbose? playful? serious? What is their communication style?"
            ),
            output_schema=SCHEMA
        )

        deadline = time.time() + timeout
        while time.time() < deadline:
            result = exa.research.get_task(task.id)
            if result.status == "completed":
                return result.data or {}
            elif result.status == "failed":
                return {"error": "Research task failed"}
            time.sleep(4)

        return {"error": "Research timed out"}
    except Exception as e:
        return {"error": str(e)}
