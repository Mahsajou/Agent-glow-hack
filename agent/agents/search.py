"""Search agent — Exa Search. Output: search.json.
Uses aspect-aware queries for the 12 portfolio aspects:
identity, skills, projects, process, impact, range, depth, credibility,
journey, personality, communication, future."""

import json
from pathlib import Path

from agent.lib.exa_client import search as exa_search
from agent.lib.logger import get_logger

logger = get_logger("agent.agents.search")


def _build_queries(name: str, context: str) -> list[str]:
    """Build aspect-aware search queries for comprehensive coverage."""
    ctx = (context or "").strip()
    base = [
        f'"{name}" portfolio projects work',
        f"{name} {ctx} professional".strip() or f"{name} professional",
        f'"{name}" about bio introduction',
    ]
    # Credibility: awards, publications, talks
    credibility = [
        f'"{name}" awards publications research',
        f'"{name}" talks conference presentation',
        f'"{name}" GitHub open source contributions',
    ]
    # Projects, impact, case studies
    projects = [
        f'"{name}" case study project outcome',
        f"{name} LinkedIn experience",
    ]
    # Personality, writing, philosophy
    personality = [
        f'"{name}" blog writing articles essays',
        f'"{name}" interview philosophy values',
    ]
    return base + credibility + projects + personality


def run(name: str, context: str, output_path: Path) -> dict:
    queries = _build_queries(name, context)
    logger.info("search name=%r context=%r queries=%d", name, context[:50] if context else "", len(queries))
    all_results = []
    seen = set()
    for q in queries:
        try:
            for r in exa_search(q, num_results=5):
                if r["url"] not in seen:
                    seen.add(r["url"])
                    all_results.append(r)
        except Exception as e:
            logger.warning("search query failed q=%r err=%s", q[:80], e)
            continue
    data = {"name": name, "context": context, "urls": [r["url"] for r in all_results], "results": all_results}
    logger.info("search done urls=%d", len(data["urls"]))
    output_path.write_text(json.dumps(data, indent=2))
    return data
