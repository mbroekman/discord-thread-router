"""Load the channel rules from rules.yaml, and reload them when the file changes."""

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .models import ActionSpec

logger = logging.getLogger(__name__)

Rules = dict[int, list[ActionSpec]]


class RulesError(ValueError):
    """rules.yaml is not valid."""


def parse_rules(data: Any, known_actions: set[str]) -> Rules:
    """Turn the parsed YAML into {channel_id: [ActionSpec, ...]}."""
    if not isinstance(data, dict) or not isinstance(data.get("channels"), dict):
        raise RulesError("rules.yaml needs a 'channels' mapping")
    rules: Rules = {}
    for channel, actions in data["channels"].items():
        try:
            channel_id = int(channel)
        except (TypeError, ValueError) as e:
            raise RulesError(f"channel id {channel!r} is not a number") from e
        if isinstance(actions, dict):
            actions = [actions]
        if not isinstance(actions, list) or not actions:
            raise RulesError(f"channel {channel_id}: give one or more actions")
        specs = []
        for entry in actions:
            if not isinstance(entry, dict) or "action" not in entry:
                raise RulesError(f"channel {channel_id}: every entry needs 'action'")
            options = dict(entry)
            name = options.pop("action")
            if name not in known_actions:
                raise RulesError(f"channel {channel_id}: unknown action {name!r}")
            specs.append(ActionSpec(name, options))
        rules[channel_id] = specs
    return rules


def legacy_rules(env: dict[str, str]) -> Rules:
    """The old .env setup: FORUM_CHANNEL_ID -> issue, DISCUSSION_CHANNEL_ID -> discussion."""
    owner, name = env.get("GITHUB_REPO_OWNER"), env.get("GITHUB_REPO_NAME")
    if not owner or not name:
        return {}
    repo = f"{owner}/{name}"
    rules: Rules = {}
    if int(env.get("FORUM_CHANNEL_ID") or 0):
        rules[int(env["FORUM_CHANNEL_ID"])] = [ActionSpec("github_issue", {"repo": repo, "title_prefix": "[Issue] "})]
    if int(env.get("DISCUSSION_CHANNEL_ID") or 0):
        rules[int(env["DISCUSSION_CHANNEL_ID"])] = [
            ActionSpec("github_discussion", {"repo": repo, "title_prefix": "[Discussion] "})
        ]
    return rules


class RulesStore:
    """Holds the current rules; reloads rules.yaml when its modification time changes.

    An invalid file is logged and the previous rules stay in force.
    """

    def __init__(self, path: Path, known_actions: set[str], env: dict[str, str] | None = None):
        self.path = path
        self.known_actions = known_actions
        self.env = dict(os.environ) if env is None else env
        self._mtime: float | None = None
        self._rules: Rules = {}
        self._loaded = False

    def get(self) -> Rules:
        try:
            mtime = self.path.stat().st_mtime
        except FileNotFoundError:
            if not self._loaded:
                self._rules = legacy_rules(self.env)
                self._loaded = True
                if self._rules:
                    logger.warning("%s not found, using the legacy .env channel ids", self.path)
            return self._rules
        if mtime != self._mtime:
            self._mtime = mtime
            try:
                data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
                self._rules = parse_rules(data, self.known_actions)
                self._loaded = True
                logger.info("Loaded %d channel rule(s) from %s", len(self._rules), self.path)
            except (yaml.YAMLError, RulesError) as e:
                logger.error("Ignoring invalid %s, keeping the previous rules: %s", self.path, e)
        return self._rules
