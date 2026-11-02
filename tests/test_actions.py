import httpx

from thread_router.actions.github import GitHubDiscussion, GitHubIssue
from thread_router.actions.kanban import KanbanCard


async def test_issue_is_created_with_prefix_labels_and_link(thread, mock_http):
    client, rec = mock_http(lambda r: httpx.Response(201, json={"html_url": "https://github.com/o/r/issues/1"}))
    options = {"repo": "o/r", "labels": ["bug"], "title_prefix": "[Issue] "}
    result = await GitHubIssue(client, "tok").handle(thread, options)
    assert result.ok and result.url == "https://github.com/o/r/issues/1"
    assert rec.requests[0].url == "https://api.github.com/repos/o/r/issues"
    assert rec.requests[0].headers["Authorization"] == "Bearer tok"
    body = rec.json()
    assert body["title"] == "[Issue] Ship explodes on undock" and body["labels"] == ["bug"]
    assert "Pilot" in body["body"] and thread.jump_url in body["body"]


async def test_issue_failure_is_a_result_not_an_exception(thread, mock_http):
    client, _ = mock_http(lambda r: httpx.Response(403, json={}))
    result = await GitHubIssue(client, "tok").handle(thread, {"repo": "o/r"})
    assert not result.ok and "403" in result.message


async def test_issue_without_repo_is_refused(thread, mock_http):
    client, rec = mock_http(lambda r: httpx.Response(201))
    assert not (await GitHubIssue(client, "tok").handle(thread, {})).ok
    assert rec.requests == []


async def test_discussion_uses_the_named_category(thread, mock_http):
    def handler(request):
        if "createDiscussion" in request.content.decode():
            return httpx.Response(200, json={"data": {"createDiscussion": {"discussion": {"url": "https://d/1"}}}})
        nodes = [{"id": "C1", "name": "General"}, {"id": "C2", "name": "Ideas"}]
        repo = {"id": "R", "discussionCategories": {"nodes": nodes}}
        return httpx.Response(200, json={"data": {"repository": repo}})

    client, rec = mock_http(handler)
    result = await GitHubDiscussion(client, "tok").handle(thread, {"repo": "o/r", "category": "ideas"})
    assert result.ok and result.url == "https://d/1"
    assert rec.json()["variables"]["catId"] == "C2"


async def test_discussion_graphql_error_fails_cleanly(thread, mock_http):
    client, _ = mock_http(lambda r: httpx.Response(200, json={"errors": [{"message": "nope"}]}))
    assert not (await GitHubDiscussion(client, "tok").handle(thread, {"repo": "o/r"})).ok


async def test_kanban_card_posts_thread_to_intake(thread, mock_http):
    reply = {
        "card_id": 12,
        "card_url": "https://auth/kanban/board/t/?card=12",
        "board_name": "Tickets",
        "skipped": ["label X"],
    }
    client, rec = mock_http(lambda r: httpx.Response(201, json=reply))
    action = KanbanCard(client, "https://auth/kanban", "key")
    result = await action.handle(thread, {"board": "t", "list": "Backlog", "labels": ["X"], "team": "IT"})
    assert result.ok and result.url == reply["card_url"]
    assert "#12" in result.message and "label X" in result.message
    assert rec.requests[0].url == "https://auth/kanban/api/intake/discord-thread/"
    assert rec.requests[0].headers["Authorization"] == "Bearer key"
    sent = rec.json()
    assert sent["board"] == "t" and sent["thread_id"] == 555 and sent["author_discord_id"] == 42


async def test_kanban_existing_card_and_errors(thread, mock_http):
    client, _ = mock_http(lambda r: httpx.Response(200, json={"card_id": 3, "card_url": "u"}))
    result = await KanbanCard(client, "https://auth/kanban/", "key").handle(thread, {"board": "t"})
    assert result.ok and "Already" in result.message

    client, _ = mock_http(lambda r: httpx.Response(404, json={"error": "Unknown board."}))
    result = await KanbanCard(client, "https://auth/kanban/", "key").handle(thread, {"board": "x"})
    assert not result.ok and "Unknown board." in result.message

    assert not (await KanbanCard(client, None, None).handle(thread, {"board": "x"})).ok
