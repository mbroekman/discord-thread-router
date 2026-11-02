"""The interface every action implements."""

from typing import Any, Protocol

from ..models import Result, ThreadInfo


class Action(Protocol):
    """Handles a new thread for one rule entry. Never raises: failures become a Result."""

    name: str

    async def handle(self, thread: ThreadInfo, options: dict[str, Any]) -> Result: ...


def thread_body(thread: ThreadInfo) -> str:
    """Markdown body with the author, the starter message and a link back to Discord."""
    content = thread.content.strip() or "No description provided."
    return (
        f"**Submitted from Discord by:** {thread.author_name}\n\n"
        f"**Content:**\n{content}\n\n"
        f"[Open the Discord thread]({thread.jump_url})"
    )
