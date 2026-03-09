"""Temporal and application configuration."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from temporalio.common import RetryPolicy


@dataclass(frozen=True)
class TemporalConfig:
    """Temporal connection and worker settings."""
    host: str = field(default_factory=lambda: os.environ.get("TEMPORAL_HOST", "localhost:7233"))
    namespace: str = field(default_factory=lambda: os.environ.get("TEMPORAL_NAMESPACE", "default"))
    task_queue: str = field(default_factory=lambda: os.environ.get("TEMPORAL_TASK_QUEUE", "persona-task-queue"))


@dataclass(frozen=True)
class ActivityTimeouts:
    """Standard timeouts for each activity type."""
    search: float = 120
    contents: float = 180
    research: float = 300
    vibe: float = 120
    symbol: float = 180
    images: float = 300
    html: float = 120
    nudge: float = 120


# Default retry policy for activities
DEFAULT_RETRY_POLICY = RetryPolicy(
    initial_interval=2.0,
    maximum_interval=30.0,
    backoff_coefficient=2.0,
    maximum_attempts=3,
    non_retryable_error_types=[],
)
