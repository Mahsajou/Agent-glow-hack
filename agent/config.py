"""Temporal and application configuration."""

import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

from temporalio.common import RetryPolicy


def _get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


@dataclass(frozen=True)
class StorageConfig:
    """Storage backend for workflow artifacts. STORAGE_BACKEND=fs|s3."""
    backend: str = field(default_factory=lambda: _get_env("STORAGE_BACKEND", "fs").lower())
    s3_bucket: str | None = field(default_factory=lambda: _get_env("S3_BUCKET") or None)
    s3_region: str | None = field(default_factory=lambda: _get_env("S3_REGION") or None)
    s3_endpoint_url: str | None = field(default_factory=lambda: _get_env("S3_ENDPOINT_URL") or None)


def _temporal_tls() -> bool:
    """Enable TLS for port 443 or when TEMPORAL_TLS=true."""
    explicit = os.environ.get("TEMPORAL_TLS", "").lower()
    if explicit in ("1", "true", "yes"):
        return True
    if explicit in ("0", "false", "no"):
        return False
    host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
    return host.endswith(":443") or host.endswith(":443/")


@dataclass(frozen=True)
class TemporalConfig:
    """Temporal connection and worker settings."""
    host: str = field(default_factory=lambda: os.environ.get("TEMPORAL_HOST", "localhost:7233"))
    namespace: str = field(default_factory=lambda: os.environ.get("TEMPORAL_NAMESPACE", "default"))
    task_queue: str = field(default_factory=lambda: os.environ.get("TEMPORAL_TASK_QUEUE", "persona-task-queue"))
    tls: bool = field(default_factory=_temporal_tls)


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
    initial_interval=timedelta(seconds=2),
    maximum_interval=timedelta(seconds=30),
    backoff_coefficient=2.0,
    maximum_attempts=3,
    non_retryable_error_types=[],
)
