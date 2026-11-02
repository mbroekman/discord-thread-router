"""Run the actions of the rule that matches a thread's channel."""

import logging

from .actions import Action
from .models import Result, ThreadInfo
from .rules import Rules

logger = logging.getLogger(__name__)


async def route(thread: ThreadInfo, rules: Rules, actions: dict[str, Action]) -> list[Result]:
    """Results of every action for this thread's channel; empty if the channel has no rule."""
    results = []
    for spec in rules.get(thread.channel_id, []):
        try:
            result = await actions[spec.action].handle(thread, spec.options)
        except Exception:  # an action must never take the bot down
            logger.exception("Action %s failed for thread %s", spec.action, thread.thread_id)
            result = Result(False, f"Action {spec.action} failed unexpectedly.")
        logger.info(
            "Thread %s in channel %s: %s %s",
            thread.thread_id,
            thread.channel_id,
            spec.action,
            "ok" if result.ok else "failed",
        )
        results.append(result)
    return results


def reply_text(results: list[Result]) -> str:
    """One reply for the thread, a line per action."""
    lines = []
    for r in results:
        icon = "✅" if r.ok else "⚠️"
        lines.append(f"{icon} {r.message}" + (f" {r.url}" if r.url else ""))
    return "\n".join(lines)
