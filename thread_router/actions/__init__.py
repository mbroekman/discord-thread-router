"""All actions the rules can use. A new action is a class with `name` and `handle`, registered here."""

import httpx

from .base import Action
from .github import GitHubDiscussion, GitHubIssue
from .kanban import KanbanCard

ACTION_NAMES = {GitHubIssue.name, GitHubDiscussion.name, KanbanCard.name}


def build_actions(client: httpx.AsyncClient, env: dict[str, str]) -> dict[str, Action]:
    actions: list[Action] = [
        GitHubIssue(client, env.get("GITHUB_TOKEN")),
        GitHubDiscussion(client, env.get("GITHUB_TOKEN")),
        KanbanCard(client, env.get("KANBAN_BASE_URL"), env.get("KANBAN_API_KEY")),
    ]
    return {a.name: a for a in actions}


__all__ = ["ACTION_NAMES", "Action", "build_actions"]
