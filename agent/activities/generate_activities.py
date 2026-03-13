"""Temporal activities for Persona portfolio generation."""

import base64
import json
from pathlib import Path

from temporalio import activity

from agent.config import StorageConfig
from agent.lib.storage import create_store


def _store(output_dir: str):
    cfg = StorageConfig()
    return create_store(
        cfg.backend,
        output_dir,
        s3_bucket=cfg.s3_bucket,
        s3_region=cfg.s3_region,
        s3_endpoint_url=cfg.s3_endpoint_url,
    )


def _path_for_agents(store):
    """Get Path for agents. For S3 yields from work_directory context."""
    from agent.lib.storage import S3Store
    if isinstance(store, S3Store):
        return store.work_directory()
    return _PathContext(store.directory())


class _PathContext:
    """No-op context for FS - just yields the path."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        return self.path

    def __exit__(self, *args):
        pass


@activity.defn
async def search_activity(name: str, context: str, output_dir: str) -> dict:
    """Search for person's public presence via Exa. Output: search.json."""
    activity.logger.info("Running search for %s", name)
    store = _store(output_dir)
    data = store.read_json("search.json")
    if data is not None:
        return data
    from agent.agents import search as search_agent
    with _path_for_agents(store) as path:
        return search_agent.run(name, context, path / "search.json")


@activity.defn
async def contents_activity(output_dir: str) -> dict:
    """Fetch page contents via Exa Contents. Output: contents.json."""
    activity.logger.info("Running contents for output_dir=%s", output_dir[:80])
    store = _store(output_dir)
    if store.exists("contents.json"):
        return store.read_json("contents.json")
    search_data = store.read_json("search.json")
    if search_data is None:
        raise FileNotFoundError(
            f"search.json not found in {output_dir}. Ensure search_activity runs and completes before contents_activity."
        )
    from agent.agents import contents as contents_agent
    with _path_for_agents(store) as path:
        return contents_agent.run(search_data, path / "contents.json")


@activity.defn
async def research_activity(name: str, context: str, output_dir: str) -> dict:
    """Deep research via Exa Research. Output: research.json."""
    activity.logger.info("Running research for %s", name)
    store = _store(output_dir)
    data = store.read_json("research.json")
    if data is not None:
        return data
    from agent.agents import research as research_agent
    with _path_for_agents(store) as path:
        return research_agent.run(name, context, path / "research.json")


@activity.defn
async def curate_activity(output_dir: str) -> dict:
    """Curate research + contents into a unified profile. Output: curated.json."""
    activity.logger.info("Running curate for output_dir=%s", output_dir[:80])
    store = _store(output_dir)
    data = store.read_json("curated.json")
    if data is not None:
        return data
    research = store.read_json("research.json")
    contents = store.read_json("contents.json")
    if research is None or contents is None:
        raise FileNotFoundError(
            f"research.json and/or contents.json not found in {output_dir}. "
            "Ensure contents_activity and research_activity complete before curate_activity."
        )
    from agent.agents import curate as curate_agent
    with _path_for_agents(store) as path:
        return curate_agent.run(research, contents, path / "curated.json")


@activity.defn
async def vibe_activity(output_dir: str) -> dict:
    """Infer aesthetic from curated profile. Output: vibe.json."""
    activity.logger.info("Running vibe for output_dir=%s", output_dir[:80])
    store = _store(output_dir)
    data = store.read_json("vibe.json")
    if data is not None:
        return data
    curated = store.read_json("curated.json")
    if curated is None:
        raise FileNotFoundError(
            f"curated.json not found in {output_dir}. Ensure curate_activity runs and completes before vibe_activity."
        )
    from agent.agents import vibe as vibe_agent
    with _path_for_agents(store) as path:
        return vibe_agent.run(curated, path / "vibe.json")


@activity.defn
async def symbol_activity(output_dir: str) -> str:
    """Generate brand symbol image. Output: symbol.png. Returns filename for html_activity to read."""
    store = _store(output_dir)
    if store.exists("symbol.png"):
        return "symbol.png"
    vibe = store.read_json("vibe.json")
    curated = store.read_json("curated.json")
    if vibe is None:
        raise FileNotFoundError(f"vibe.json not found in {output_dir}. Ensure vibe_activity runs before symbol_activity.")
    if curated is None:
        raise FileNotFoundError(f"curated.json not found in {output_dir}. Ensure curate_activity runs before symbol_activity.")
    from agent.agents import symbol as symbol_agent
    with _path_for_agents(store) as path:
        symbol_agent.run(vibe, curated, path / "symbol.png")
    return "symbol.png" if store.exists("symbol.png") else ""


@activity.defn
async def images_activity(output_dir: str) -> tuple[list[str], str | None]:
    """Generate banner and moodboard images. Returns (filenames, error)."""
    activity.logger.info("Running images for output_dir=%s", output_dir[:80])
    store = _store(output_dir)
    filenames: list[str] = []
    if store.exists("banner.png"):
        filenames.append("banner.png")
    if store.exists("moodboard.png"):
        filenames.append("moodboard.png")
    if filenames:
        return filenames, None
    vibe = store.read_json("vibe.json")
    curated = store.read_json("curated.json")
    if vibe is None:
        raise FileNotFoundError(f"vibe.json not found in {output_dir}. Ensure vibe_activity runs before images_activity.")
    if curated is None:
        raise FileNotFoundError(f"curated.json not found in {output_dir}. Ensure curate_activity runs before images_activity.")
    from agent.agents import images as images_agent
    with _path_for_agents(store) as path:
        _, err = images_agent.run(vibe, curated, path, max_images=2)
    filenames = []
    if store.exists("banner.png"):
        filenames.append("banner.png")
    if store.exists("moodboard.png"):
        filenames.append("moodboard.png")
    return filenames, err


def _blob_to_data_uri(data: bytes) -> str:
    """Convert image bytes to data URI."""
    return f"data:image/png;base64,{base64.b64encode(data).decode('ascii')}"


@activity.defn
async def html_activity(output_dir: str, image_filenames: list[str], symbol_filename: str) -> str:
    """Generate portfolio HTML. Returns empty to avoid Temporal payload limit."""
    activity.logger.info("Running html output_dir=%s images=%d symbol=%s", output_dir[:80], len(image_filenames), bool(symbol_filename))
    store = _store(output_dir)
    if store.exists("portfolio.html"):
        html = store.read_blob("portfolio.html")
        if html and b"data:image" in html:
            return ""
    images: list[str] | None = None
    if image_filenames:
        images = []
        for f in image_filenames:
            b = store.read_blob(f)
            if b is not None:
                images.append(_blob_to_data_uri(b))
    symbol_uri = None
    if symbol_filename:
        b = store.read_blob(symbol_filename)
        if b is not None:
            symbol_uri = _blob_to_data_uri(b)
    curated = store.read_json("curated.json")
    vibe = store.read_json("vibe.json")
    if curated is None:
        raise FileNotFoundError(f"curated.json not found in {output_dir}. Ensure curate_activity runs before html_activity.")
    if vibe is None:
        raise FileNotFoundError(f"vibe.json not found in {output_dir}. Ensure vibe_activity runs before html_activity.")
    from agent.agents import html as html_agent
    with _path_for_agents(store) as path:
        html_agent.run(curated, vibe, path / "portfolio.html", images=images, symbol_img=symbol_uri)
    return ""
