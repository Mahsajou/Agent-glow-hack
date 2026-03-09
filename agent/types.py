"""Temporal workflow and activity input/output types (JSON-serializable)."""

from dataclasses import dataclass, field
from typing import Any


# --- Generate workflow ---

@dataclass(frozen=True)
class GenerateInput:
    """Input for PersonaGenerateWorkflow."""
    name: str
    context: str = ""
    output_dir: str = ""


@dataclass
class GenerateResult:
    """Result of PersonaGenerateWorkflow."""
    html: str
    output_dir: str
    images_count: int = 0
    error: str | None = None


# --- Nudge workflow ---

@dataclass(frozen=True)
class NudgeInput:
    """Input for PersonaNudgeWorkflow."""
    nudge_id: str
    output_dir: str


@dataclass
class NudgeResult:
    """Result of PersonaNudgeWorkflow."""
    html: str
    nudge_id: str
    output_dir: str
    error: str | None = None


# --- Activity input types (for type hints; activities receive raw args from workflow) ---

@dataclass(frozen=True)
class SearchParams:
    name: str
    context: str
    output_dir: str


@dataclass(frozen=True)
class HtmlParams:
    output_dir: str
    images: list[str] = field(default_factory=list)
    symbol_uri: str = ""
