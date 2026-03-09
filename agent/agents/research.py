"""Research agent — Exa Research. Output: research.json"""

import json
from pathlib import Path

from agent.lib.exa_client import research as exa_research


def run(name: str, context: str, output_path: Path) -> dict:
    instructions = f"""Research {name} professionally and personally.
Find and extract: full name, current role, company, bio (2-4 sentences), skills, notable projects, education, social links, achievements, writing samples, interests/hobbies, personality notes.
{f'Context: {context}' if context else ''}
Use ONLY information found from web sources. Never invent. Be thorough but concise."""
    data = exa_research(instructions)
    output_path.write_text(json.dumps(data, indent=2))
    return data
