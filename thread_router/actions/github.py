"""GitHub actions: an issue (REST) or a discussion (GraphQL)."""

import logging
from typing import Any

import httpx

from ..models import Result, ThreadInfo
from .base import thread_body

logger = logging.getLogger(__name__)

API = "https://api.github.com"


class _GitHubAction:
    def __init__(self, client: httpx.AsyncClient, token: str | None):
        self.client = client
        self.token = token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}

    def _repo(self, options: dict[str, Any]) -> tuple[str, str] | None:
        owner, _, name = str(options.get("repo", "")).partition("/")
        return (owner, name) if owner and name else None


class GitHubIssue(_GitHubAction):
    name = "github_issue"

    async def handle(self, thread: ThreadInfo, options: dict[str, Any]) -> Result:
        repo = self._repo(options)
        if not self.token or not repo:
            return Result(False, "GitHub issue: no token or no 'repo: owner/name' configured.")
        payload: dict[str, Any] = {
            "title": f"{options.get('title_prefix', '')}{thread.title}",
            "body": thread_body(thread),
        }
        if options.get("labels"):
            payload["labels"] = list(options["labels"])
        try:
            response = await self.client.post(
                f"{API}/repos/{repo[0]}/{repo[1]}/issues", json=payload, headers=self._headers()
            )
        except httpx.HTTPError as e:
            logger.warning("GitHub issue for thread %s failed: %s", thread.thread_id, e)
            return Result(False, "Could not reach GitHub to create the issue.")
        if response.status_code != 201:
            logger.warning("GitHub issue for thread %s: HTTP %s", thread.thread_id, response.status_code)
            return Result(False, f"GitHub refused the issue (HTTP {response.status_code}).")
        return Result(True, "Forwarded to GitHub as an issue.", response.json().get("html_url"))


class GitHubDiscussion(_GitHubAction):
    name = "github_discussion"

    CATEGORIES = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        id
        discussionCategories(first: 25) { nodes { id name } }
      }
    }"""
    CREATE = """
    mutation($repoId: ID!, $catId: ID!, $title: String!, $body: String!) {
      createDiscussion(input: {repositoryId: $repoId, categoryId: $catId, title: $title, body: $body}) {
        discussion { url }
      }
    }"""

    async def _graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(
            f"{API}/graphql", json={"query": query, "variables": variables}, headers=self._headers()
        )
        response.raise_for_status()
        body = response.json()
        if body.get("errors"):
            raise httpx.HTTPError(str(body["errors"][0].get("message", "GraphQL error")))
        return body.get("data") or {}

    async def handle(self, thread: ThreadInfo, options: dict[str, Any]) -> Result:
        repo = self._repo(options)
        if not self.token or not repo:
            return Result(False, "GitHub discussion: no token or no 'repo: owner/name' configured.")
        try:
            data = await self._graphql(self.CATEGORIES, {"owner": repo[0], "name": repo[1]})
            repository = data.get("repository") or {}
            categories = repository.get("discussionCategories", {}).get("nodes") or []
            if not categories:
                return Result(False, "The repository has no discussion categories (are Discussions enabled?).")
            wanted = str(options.get("category", "")).lower()
            category = next((c for c in categories if c["name"].lower() == wanted), categories[0])
            data = await self._graphql(
                self.CREATE,
                {
                    "repoId": repository["id"],
                    "catId": category["id"],
                    "title": f"{options.get('title_prefix', '')}{thread.title}",
                    "body": thread_body(thread),
                },
            )
        except (httpx.HTTPError, KeyError) as e:
            logger.warning("GitHub discussion for thread %s failed: %s", thread.thread_id, e)
            return Result(False, "Could not create the discussion on GitHub.")
        url = (data.get("createDiscussion") or {}).get("discussion", {}).get("url")
        if not url:
            return Result(False, "GitHub did not return the new discussion.")
        return Result(True, "Forwarded to GitHub as a discussion.", url)
