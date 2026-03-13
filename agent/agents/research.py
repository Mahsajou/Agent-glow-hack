"""Research agent — Exa Research. Output: research.json.
Extracts data for all 12 portfolio aspects."""

import json
from pathlib import Path

from agent.lib.exa_client import research as exa_research
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.research")

RESEARCH_INSTRUCTIONS_TEMPLATE = """Research {name} professionally and personally. Extract structured data for these 12 portfolio aspects:

1. IDENTITY: full_name, current_role, company, bio (2-4 sentences), mission_statement, focus_areas, values
2. SKILLS: skills, tools_technologies, methodologies, domain_expertise
3. PROJECTS: For each project provide: name, description, outcome, impact_metrics (quantified), process_notes, url, role. Also include notable_projects as fallback strings
4. PROCESS: Include process_notes per project — how they think (problem→solution, research→design, etc.)
5. IMPACT: achievements, impact_statements — quantified outcomes (e.g. "reduced latency 60%", "cited 200+ times")
6. RANGE: industries, project_types — diversity of work
7. DEPTH: specialization — mastery area, signature style
8. CREDIBILITY: awards, publications, talks_presentations, certifications, testimonials, media_coverage, education, social_links
9. JOURNEY: career_highlights, learning_milestones — progression over time
10. PERSONALITY: interests_hobbies, personality_notes, personal_philosophy
11. COMMUNICATION: writing_samples — essays, blog posts, clarity of expression
12. FUTURE: future_vision, research_interests — where they want to go next

{context_section}

Use ONLY information from web sources. Never invent. Prioritize evidence (URLs, metrics) over claims. Be thorough."""


def run(name: str, context: str, output_path: Path) -> dict:
    logger.info("research name=%r context=%r", name, (context or "")[:50])
    ctx = (context or "").strip()
    context_section = f"Context/profession: {ctx}" if ctx else ""
    instructions = RESEARCH_INSTRUCTIONS_TEMPLATE.format(
        name=name, context_section=context_section
    )
    data = exa_research(instructions)
    has_err = data.get("error")
    logger.info("research done has_error=%s", bool(has_err))
    output_path.write_text(json.dumps(data, indent=2))
    return data
