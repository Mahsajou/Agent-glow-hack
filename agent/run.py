#!/usr/bin/env python3
"""
Persona Temporal Worker — production-ready.

Usage:
  python run.py worker                    # Run the worker
  python run.py start <name> [context]    # Start generate workflow
  python run.py nudge <nudge_id>          # Start nudge workflow
"""

import asyncio
import os
import re
import sys
from pathlib import Path

# Ensure project root on path
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Load env before imports
if "GMI_API_KEY" not in os.environ or "EXA_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    for p in [_root / ".env.local", Path(__file__).parent / ".env.local"]:
        if p.exists():
            load_dotenv(p)
            break

from temporalio.client import Client
from temporalio.worker import Worker

from agent.config import TemporalConfig
from agent.workflows.persona_workflow import PersonaGenerateWorkflow, PersonaNudgeWorkflow
from agent.activities.generate_activities import (
    search_activity,
    contents_activity,
    research_activity,
    vibe_activity,
    symbol_activity,
    images_activity,
    html_activity,
)
from agent.activities.nudge_activities import nudge_activity


OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

CONFIG = TemporalConfig()


def _workflow_id(slug: str) -> str:
    """Generate a deterministic workflow ID from a slug."""
    safe = re.sub(r"[^a-z0-9-]", "-", slug.lower())[:80]
    return f"persona-{safe}-{hash(slug) % 100000:05d}"


async def run_worker() -> None:
    """Run the Temporal worker."""
    client = await Client.connect(
        CONFIG.host,
        namespace=CONFIG.namespace,
    )
    worker = Worker(
        client,
        task_queue=CONFIG.task_queue,
        workflows=[PersonaGenerateWorkflow, PersonaNudgeWorkflow],
        activities=[
            search_activity,
            contents_activity,
            research_activity,
            vibe_activity,
            symbol_activity,
            images_activity,
            html_activity,
            nudge_activity,
        ],
    )
    print(f"Worker started. Task queue: {CONFIG.task_queue}", flush=True)
    await worker.run()


async def start_generate(name: str, context: str = "") -> dict:
    """Start a generate workflow and wait for result."""
    client = await Client.connect(CONFIG.host, namespace=CONFIG.namespace)
    wf_id = _workflow_id(f"generate-{name}-{context}")
    handle = await client.start_workflow(
        PersonaGenerateWorkflow.run,
        args=[name, context, str(OUTPUT_DIR)],
        id=wf_id,
        task_queue=CONFIG.task_queue,
    )
    print(f"Started workflow: {handle.id}", flush=True)
    result = await handle.result()
    html_len = len(result.get("html", ""))
    print(f"Done. HTML length: {html_len}", flush=True)
    return result


async def start_nudge(nudge_id: str) -> dict:
    """Start a nudge workflow and wait for result."""
    client = await Client.connect(CONFIG.host, namespace=CONFIG.namespace)
    wf_id = _workflow_id(f"nudge-{nudge_id}")
    handle = await client.start_workflow(
        PersonaNudgeWorkflow.run,
        args=[nudge_id, str(OUTPUT_DIR)],
        id=wf_id,
        task_queue=CONFIG.task_queue,
    )
    print(f"Started workflow: {handle.id}", flush=True)
    result = await handle.result()
    print(f"Done. HTML length: {len(result.get('html', ''))}", flush=True)
    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python run.py worker | start <name> [context] | nudge <nudge_id>")
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
        if len(sys.argv) < 3:
            print("Usage: python run.py nudge <nudge_id>")
            sys.exit(1)
        nudge_id = sys.argv[2]
        asyncio.run(start_nudge(nudge_id))
    else:
        print("Unknown command. Use: worker | start | nudge")
        sys.exit(1)


if __name__ == "__main__":
    main()
