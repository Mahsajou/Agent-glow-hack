"""Contents agent — Exa get_contents. Output: contents.json. Indexes to RAG."""

import json
from pathlib import Path

from agent.lib.exa_client import get_contents
from agent.lib.logger import get_logger
from agent.lib.rag import chunk_contents, index_chunks

logger = get_logger("agent.agents.contents")


def run(search_data: dict, output_path: Path, run_id: str) -> dict:
    urls = search_data.get("urls", [])
    if not urls:
        data = {"urls": [], "contents": {}}
        output_path.write_text(json.dumps(data, indent=2))
        return data
    contents = get_contents(urls)
    has_err = "error" in contents
    logger.info("contents done entries=%d has_error=%s", len(contents), has_err)
    data = {"urls": urls, "contents": contents}
    output_path.write_text(json.dumps(data, indent=2))
    if not has_err:
        chunks = chunk_contents(data)
        if chunks:
            n = index_chunks(run_id, chunks)
            logger.info("contents indexed run_id=%s chunks=%d", run_id, n)
    return data
