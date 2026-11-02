"""Kanban action: create a card on an aa-kanban board through its intake API."""

import logging
from typing import Any

import httpx

from ..models import Result, ThreadInfo

logger = logging.getLogger(__name__)

INTAKE_PATH = "api/intake/discord-thread/"


class KanbanCard:
    name = "kanban_card"

    def __init__(self, client: httpx.AsyncClient, base_url: str | None, api_key: str | None):
        self.client = client
        self.base_url = (base_url or "").rstrip("/") + "/"
        self.api_key = api_key

    async def handle(self, thread: ThreadInfo, options: dict[str, Any]) -> Result:
        if not self.api_key or self.base_url == "/" or not options.get("board"):
            return Result(False, "Kanban: KANBAN_BASE_URL, KANBAN_API_KEY or 'board' is not configured.")
        payload = {
            "board": options["board"],
            "list": options.get("list", ""),
            "labels": list(options.get("labels") or []),
            "team": options.get("team", ""),
            "thread_id": thread.thread_id,
            "title": thread.title,
            "content": thread.content,
            "author_discord_id": thread.author_id,
            "author_name": thread.author_name,
            "jump_url": thread.jump_url,
        }
        try:
            response = await self.client.post(
                self.base_url + INTAKE_PATH,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
        except httpx.HTTPError as e:
            logger.warning("Kanban card for thread %s failed: %s", thread.thread_id, e)
            return Result(False, "Could not reach the kanban board.")
        if response.status_code not in (200, 201):
            logger.warning("Kanban card for thread %s: HTTP %s", thread.thread_id, response.status_code)
            detail = ""
            try:
                detail = response.json().get("error", "")
            except ValueError:
                pass
            return Result(False, f"The kanban board refused the card (HTTP {response.status_code}). {detail}".strip())
        body = response.json()
        message = f"Card #{body.get('card_id')} created on board {body.get('board_name', options['board'])}."
        if response.status_code == 200:
            message = f"Already on the board as card #{body.get('card_id')}."
        if body.get("skipped"):
            message += f" Not found and skipped: {', '.join(body['skipped'])}."
        return Result(True, message, body.get("card_url"))
