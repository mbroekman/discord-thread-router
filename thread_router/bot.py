"""The Discord side: listen for new threads and hand them to the router."""

import asyncio
import logging
import os
from collections import OrderedDict
from pathlib import Path

import discord
import httpx
from dotenv import load_dotenv

from .actions import ACTION_NAMES, Action, build_actions
from .models import ThreadInfo
from .router import reply_text, route
from .rules import RulesStore

logger = logging.getLogger(__name__)

# Discord may send the same thread twice (reconnects); GitHub has no duplicate check.
SEEN_LIMIT = 1000


async def starter_message(thread: discord.Thread) -> discord.Message | None:
    """The message that opened the thread.

    In a forum and for a thread made from a message, it has the thread's id. Discord
    can deliver it just after the thread event, so try a few times.
    """
    sources: list[discord.Thread | discord.TextChannel] = [thread]
    if isinstance(thread.parent, discord.TextChannel):
        sources.append(thread.parent)
    for _ in range(3):
        for source in sources:
            try:
                return await source.fetch_message(thread.id)
            except (discord.NotFound, discord.Forbidden):
                pass
        await asyncio.sleep(1)
    # A thread without a starter message: take its first message, if there is one.
    async for message in thread.history(limit=1, oldest_first=True):
        return message
    return None


class ThreadRouterBot(discord.Client):
    def __init__(self, rules: RulesStore, env: dict[str, str]):
        intents = discord.Intents.default()
        intents.message_content = True  # needed to read the starter message
        super().__init__(intents=intents)
        self.rules = rules
        self.env = env
        self.http_client: httpx.AsyncClient | None = None
        self.actions: dict[str, Action] = {}
        self._seen: OrderedDict[int, None] = OrderedDict()

    async def setup_hook(self) -> None:
        self.http_client = httpx.AsyncClient(timeout=20)
        self.actions = build_actions(self.http_client, self.env)

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.aclose()
        await super().close()

    async def on_ready(self) -> None:
        rules = self.rules.get()
        logger.info("Logged in as %s; %d channel rule(s)", self.user, len(rules))
        for guild in self.guilds:
            for channel_id in rules:
                channel = guild.get_channel(channel_id)
                if channel:
                    logger.info("Listening on #%s (%s) in %s", channel.name, channel_id, guild.name)

    def _first_time(self, thread_id: int) -> bool:
        if thread_id in self._seen:
            return False
        self._seen[thread_id] = None
        if len(self._seen) > SEEN_LIMIT:
            self._seen.popitem(last=False)
        return True

    async def on_thread_create(self, thread: discord.Thread) -> None:
        rules = self.rules.get()
        if thread.parent_id not in rules or not self._first_time(thread.id):
            return
        if self.user and thread.owner_id == self.user.id:
            return
        message = await starter_message(thread)
        if message and message.author.bot:
            return  # e.g. ticket threads that aa-kanban opens itself
        info = ThreadInfo(
            thread_id=thread.id,
            channel_id=thread.parent_id,
            title=thread.name,
            content=message.content if message else "",
            author_name=message.author.display_name if message else "Unknown",
            author_id=message.author.id if message else thread.owner_id,
            jump_url=thread.jump_url,
            tags=tuple(tag.name for tag in getattr(thread, "applied_tags", [])),
        )
        results = await route(info, rules, self.actions)
        if results:
            try:
                await thread.send(reply_text(results))
            except discord.HTTPException as e:
                logger.warning("Could not reply in thread %s: %s", thread.id, e)


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("discord").setLevel(logging.WARNING)
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise SystemExit("DISCORD_TOKEN is not set")
    env = dict(os.environ)
    rules = RulesStore(Path(os.getenv("RULES_FILE", "rules.yaml")), ACTION_NAMES, env)
    ThreadRouterBot(rules, env).run(token, log_handler=None)
