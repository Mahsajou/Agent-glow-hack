"""Curate agent — RAG retrieve + LLM synthesize. Output: curated.json.

Input:
- research: structured data from Exa Research (RESEARCH_OUTPUT_SCHEMA)
- chunks: retrieved from RAG (or truncation fallback when RAG disabled)

Output:
- curated.json: same overall shape as research, enriched from chunks.
"""

import json
from pathlib import Path

from agent.lib.openai_client import OpenAIClient, OPENAI_LLM_MODEL
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.curate")

SCHEMA_KEYS = """full_name, current_role, company, bio, mission_statement, focus_areas, values,
  skills, tools_technologies, methodologies, domain_expertise,
  projects (array of objects: name, description, outcome, impact_metrics, process_notes, url, role),
  notable_projects, achievements, impact_statements,
  industries, project_types, specialization,
  awards, publications, talks_presentations, certifications, testimonials, media_coverage,
  education, social_links,
  career_highlights, learning_milestones,
  writing_samples, interests_hobbies, personality_notes, personal_philosophy,
  future_vision, research_interests"""


def _format_chunks(chunks: list[dict]) -> str:
    """Format chunks for prompt."""
    lines = []
    for i, c in enumerate(chunks, 1):
        url = c.get("url", "")
        src = c.get("metadata", {}).get("source", "content")
        text = (c.get("chunk_text") or "").strip()
        if text:
            lines.append(f"[{i}] URL: {url} | Source: {src}\n{text}")
    return "\n---\n".join(lines) if lines else "(no retrieved content)"


def run(research: dict, chunks: list[dict], output_path: Path) -> dict:
    """Synthesize curated profile from research + retrieved chunks via LLM."""
    client = OpenAIClient()
    formatted = _format_chunks(chunks)

    prompt = f"""You are a portfolio curator. Produce a single CURATED profile JSON from RESEARCH (primary structure) and RETRIEVED CHUNKS (evidence from web content).

Rules:
- Use RESEARCH as the base structure.
- Enrich and fill gaps using RETRIEVED CHUNKS when you have clear evidence.
- Add logical derived data where appropriate (e.g. infer impact from descriptions).
- Deduplicate overlapping items. Do NOT invent facts.
- Output schema: {SCHEMA_KEYS}

RESEARCH:
{json.dumps(research, indent=2)}

RETRIEVED CHUNKS (evidence):
{formatted}

Return ONLY the curated JSON object. No markdown, no explanation."""

    text = client.generate_content(prompt, model=OPENAI_LLM_MODEL)
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    i, j = text.find("{"), text.rfind("}") + 1
    if i >= 0 and j > i:
        text = text[i:j]
    data = json.loads(text)
    logger.info("curate done has_projects=%s chunks_used=%d", bool(data.get("projects")), len(chunks))
    output_path.write_text(json.dumps(data, indent=2))
    return data
