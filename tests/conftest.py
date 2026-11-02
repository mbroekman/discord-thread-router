import json
from collections.abc import Callable

import httpx
import pytest

from thread_router.models import ThreadInfo


@pytest.fixture
def thread() -> ThreadInfo:
    return ThreadInfo(
        thread_id=555,
        channel_id=100,
        title="Ship explodes on undock",
        content="Steps to reproduce...",
        author_name="Pilot",
        author_id=42,
        jump_url="https://discord.com/channels/1/555",
    )


class Recorder:
    """httpx transport that answers with a handler and keeps the requests."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]):
        self.handler = handler
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.handler(request)

    def json(self, i: int = -1) -> dict:
        return json.loads(self.requests[i].content)


@pytest.fixture
def mock_http():
    def make(handler: Callable[[httpx.Request], httpx.Response]) -> tuple[httpx.AsyncClient, Recorder]:
        recorder = Recorder(handler)
        return httpx.AsyncClient(transport=httpx.MockTransport(recorder)), recorder

    return make
