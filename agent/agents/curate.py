"""Curate agent — merges Exa contents + research into a unified profile.

Input:
- research: structured data from Exa Research (RESEARCH_OUTPUT_SCHEMA)
- contents: raw page contents from Exa get_contents (see contents.json)

Output:
- curated.json: same overall shape as research, but:
  - filled with additional facts from contents
  - deduplicated and cleaned
  - enriched with evidence where available
"""

import json
from pathlib import Path

from agent.lib.openai_client import OpenAIClient, OPENAI_LLM_MODEL
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.curate")


def run(research: dict, contents: dict, output_path: Path) -> dict:
    """Merge research + contents into a single curated profile JSON."""
    client = OpenAIClient()

    prompt = f"""You are a portfolio curator.
You are given:
- RESEARCH: structured data about a person (fields like full_name, bio, skills, projects, etc.)
- CONTENTS: raw page contents fetched from the web (text, summaries, highlights).

Your job:
- Produce a single CURATED profile JSON suitable for powering a personal portfolio.
- Use RESEARCH as the primary structure, but:
  - Fill in missing fields using CONTENTS when you have clear evidence.
  - Enrich projects with better descriptions, outcomes, impact_metrics, and urls when found.
  - Deduplicate overlapping items.
  - Do NOT invent facts: only include information that appears in either RESEARCH or CONTENTS.

Schema:
- Match the same overall shape as RESEARCH, especially these keys:
  full_name, current_role, company, bio, mission_statement, focus_areas, values,
  skills, tools_technologies, methodologies, domain_expertise,
  projects (array of objects: name, description, outcome, impact_metrics, process_notes, url, role),
  notable_projects, achievements, impact_statements,
  industries, project_types, specialization,
  awards, publications, talks_presentations, certifications, testimonials, media_coverage,
  education, social_links,
  career_highlights, learning_milestones,
  writing_samples, interests_hobbies, personality_notes, personal_philosophy,
  future_vision, research_interests.

Input RESEARCH:
{json.dumps(research, indent=2)}

Input CONTENTS (map url -> {{text, summary, highlights}}):
{json.dumps(contents, indent=2)}

Return ONLY the curated JSON object. No markdown, no explanation."""

    text = client.generate_content(prompt, model=OPENAI_LLM_MODEL)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    i, j = text.find("{"), text.rfind("}") + 1
    if i >= 0 and j > i:
        text = text[i:j]
    data = json.loads(text)
    logger.info("curate done has_projects=%s", bool(data.get("projects")))
    output_path.write_text(json.dumps(data, indent=2))
    return data

