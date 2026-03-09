"""Persona portfolio generation and nudge workflows."""

from dataclasses import asdict
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

from agent.config import ActivityTimeouts, DEFAULT_RETRY_POLICY
from agent.types import GenerateInput, GenerateResult, NudgeInput, NudgeResult

with workflow.imports_passed_through():
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


TIMEOUTS = ActivityTimeouts()


@workflow.defn
class PersonaGenerateWorkflow:
    """Portfolio generation workflow: search → contents → research → vibe → symbol → images → html."""

    @workflow.run
    async def run(self, name: str, context: str, output_dir: str) -> dict:
        """
        Run the full persona portfolio generation pipeline.
        Returns GenerateResult as dict for JSON serialization.
        """
        workflow.logger.info("Starting generate workflow for %s", name)

        await workflow.execute_activity(
            search_activity,
            args=[name, context, output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.search),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        await workflow.execute_activity(
            contents_activity,
            args=[output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.contents),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        await workflow.execute_activity(
            research_activity,
            args=[name, context, output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.research),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        await workflow.execute_activity(
            vibe_activity,
            args=[output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.vibe),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        symbol_uri = await workflow.execute_activity(
            symbol_activity,
            args=[output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.symbol),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        images, img_err = await workflow.execute_activity(
            images_activity,
            args=[output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.images),
            retry_policy=DEFAULT_RETRY_POLICY,
        )
        if img_err:
            workflow.logger.warning("Images activity: %s", img_err)

        html = await workflow.execute_activity(
            html_activity,
            args=[output_dir, images or [], symbol_uri or ""],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.html),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        result = GenerateResult(
            html=html,
            output_dir=output_dir,
            images_count=len(images or []),
        )
        return asdict(result)


@workflow.defn
class PersonaNudgeWorkflow:
    """Nudge workflow: patch portfolio HTML based on nudge_id."""

    @workflow.run
    async def run(self, nudge_id: str, output_dir: str) -> dict:
        """
        Apply a nudge (design patch) to the portfolio.
        Returns NudgeResult as dict for JSON serialization.
        """
        workflow.logger.info("Starting nudge workflow: %s", nudge_id)

        html = await workflow.execute_activity(
            nudge_activity,
            args=[nudge_id, output_dir],
            start_to_close_timeout=timedelta(seconds=TIMEOUTS.nudge),
            retry_policy=DEFAULT_RETRY_POLICY,
        )

        result = NudgeResult(
            html=html,
            nudge_id=nudge_id,
            output_dir=output_dir,
        )
        return asdict(result)
