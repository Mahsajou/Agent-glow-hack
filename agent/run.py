#!/usr/bin/env python3
"""
Persona Temporal Worker — production-ready.

Usage:
  python run.py worker                    # Run the worker
  python run.py start <name> [context]    # Start generate workflow
  python run.py nudge <nudge_id>          # Start nudge workflow
"""

import asyncio
import logging
import os
import sys
import uuid
from pathlib import Path

# Ensure project root on path before any agent imports
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agent.lib.logger import get_logger

# Load env before imports
required = ["OPENAI_API_KEY", "GMI_API_KEY", "EXA_API_KEY"]
if any(k not in os.environ for k in required):
    from dotenv import load_dotenv
    for p in [_root / ".env.local", Path(__file__).parent / ".env.local"]:
        if p.exists():
            load_dotenv(p)
            break

from temporalio.client import Client
from temporalio.worker import Worker

from agent.config import TemporalConfig
from agent.lib.precheck import run_prechecks
from agent.workflows.persona_workflow import PersonaGenerateWorkflow, PersonaNudgeWorkflow
from agent.activities.generate_activities import (
    search_activity,
    contents_activity,
    research_activity,
    curate_activity,
    vibe_activity,
    symbol_activity,
    images_activity,
    html_activity,
)
from agent.activities.nudge_activities import nudge_activity


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIG = TemporalConfig()
logger = get_logger("agent.run")

# Base prefix for output (fs: local dir; s3: key prefix). Workflow appends /{run_id}.
# Use AGENT_OUTPUT_DIR for S3; otherwise agent/output for local fs.
BASE_PREFIX = os.environ.get("AGENT_OUTPUT_DIR", str(OUTPUT_DIR))


async def run_worker() -> None:
    """Run the Temporal worker."""
    errors = run_prechecks()
    if errors:
        for e in errors:
            logger.error("Precheck failed: %s", e)
        sys.exit(1)
    logger.info("Prechecks passed")
    logger.info("Connecting to Temporal host=%s namespace=%s tls=%s", CONFIG.host, CONFIG.namespace, CONFIG.tls)
    client = await Client.connect(
        CONFIG.host,
        namespace=CONFIG.namespace,
        tls=CONFIG.tls,
    )
    logger.info("Temporal connected, starting worker task_queue=%s", CONFIG.task_queue)
    worker = Worker(
        client,
        task_queue=CONFIG.task_queue,
        workflows=[PersonaGenerateWorkflow, PersonaNudgeWorkflow],
        activities=[
            search_activity,
            contents_activity,
            research_activity,
            curate_activity,
            vibe_activity,
            symbol_activity,
            images_activity,
            html_activity,
            nudge_activity,
        ],
    )
    logger.info("Worker started, polling for tasks on queue=%s base_prefix=%s", CONFIG.task_queue, BASE_PREFIX)
    await worker.run()


async def start_generate(name: str, context: str = "") -> dict:
    """Start a generate workflow and wait for result. output_dir = BASE_PREFIX/{run_id}."""
    client = await Client.connect(CONFIG.host, namespace=CONFIG.namespace, tls=CONFIG.tls)
    wf_id = f"persona-generate-{uuid.uuid4()}"
    handle = await client.start_workflow(
        PersonaGenerateWorkflow.run,
        args=[name, context, BASE_PREFIX],
        id=wf_id,
        task_queue=CONFIG.task_queue,
    )
    logger.info("Started workflow id=%s name=%s", handle.id, name)
    result = await handle.result()
    output_dir = result.get("output_dir", "")
    html_len = len(result.get("html", ""))
    logger.info("Workflow complete id=%s output_dir=%s html_len=%d", handle.id, output_dir, html_len)
    return result


async def start_nudge(nudge_id: str, output_dir: str) -> dict:
    """Start a nudge workflow. output_dir from generate result (e.g. BASE_PREFIX/{run_id})."""
    client = await Client.connect(CONFIG.host, namespace=CONFIG.namespace, tls=CONFIG.tls)
    wf_id = f"persona-nudge-{uuid.uuid4()}"
    handle = await client.start_workflow(
        PersonaNudgeWorkflow.run,
        args=[nudge_id, output_dir],
        id=wf_id,
        task_queue=CONFIG.task_queue,
    )
    logger.info("Started nudge workflow id=%s nudge_id=%s output_dir=%s", handle.id, nudge_id, output_dir)
    result = await handle.result()
    html_len = len(result.get("html", ""))
    logger.info("Nudge complete id=%s html_len=%d", handle.id, html_len)
    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run.py worker | start <name> [context] | nudge <nudge_id> <output_dir>")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "worker":
        asyncio.run(run_worker())
    elif cmd == "start":
        if len(sys.argv) < 3:
            print("Usage: python run.py start <name> [context]")
            sys.exit(1)
        name = sys.argv[2]
        context = sys.argv[3] if len(sys.argv) > 3 else ""
        asyncio.run(start_generate(name, context))
    elif cmd == "nudge":
        if len(sys.argv) < 4:
            print("Usage: python run.py nudge <nudge_id> <output_dir>  # output_dir from generate result")
            sys.exit(1)
        nudge_id = sys.argv[2]
        output_dir = sys.argv[3]
        asyncio.run(start_nudge(nudge_id, output_dir))
    else:
        print("Unknown command. Use: worker | start | nudge")
        sys.exit(1)


if __name__ == "__main__":
    main()
