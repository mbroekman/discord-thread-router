"""Data passed between the Discord side and the actions."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ThreadInfo:
    """A newly opened Discord thread and its starter message."""

    thread_id: int
    channel_id: int
    title: str
    content: str
    author_name: str
    author_id: int | None
    jump_url: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ActionSpec:
    """One action from rules.yaml: its type and its options."""

    action: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Result:
    """What an action did, for the reply in the thread."""

    ok: bool
    message: str
    url: str | None = None
