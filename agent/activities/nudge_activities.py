"""Temporal activities for nudge (patch HTML)."""

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


@activity.defn
async def nudge_activity(nudge_id: str, output_dir: str) -> str:
    """Apply nudge, write portfolio.jsx. Returns empty to avoid Temporal payload limit."""
    activity.logger.info("Running nudge nudge_id=%s output_dir=%s", nudge_id, output_dir[:80])
    from agent.agents import nudge as nudge_agent

    store = _store(output_dir)
    curated = store.read_json("curated.json")
    vibe = store.read_json("vibe.json")
    html_blob = store.read_blob("portfolio.jsx")
    if curated is None or vibe is None or html_blob is None:
        return ""
    html = html_blob.decode("utf-8")
    new_html = nudge_agent.run(nudge_id, html, curated, vibe)
    store.write_blob("portfolio.jsx", new_html.encode("utf-8"))
    return ""


