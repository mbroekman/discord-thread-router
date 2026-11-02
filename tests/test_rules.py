import os
import time

import pytest

from thread_router.actions import ACTION_NAMES
from thread_router.models import ActionSpec
from thread_router.rules import RulesError, RulesStore, legacy_rules, parse_rules

RULE_ONE = 'channels:\n  "1":\n    - action: github_issue\n      repo: o/r\n'
RULE_TWO = 'channels:\n  "2":\n    - action: kanban_card\n      board: b\n'


def test_parse_rules_maps_channels_to_actions():
    rules = parse_rules(
        {
            "channels": {
                "100": [{"action": "github_issue", "repo": "o/r"}, {"action": "kanban_card", "board": "b"}],
                200: {"action": "github_discussion", "repo": "o/r"},
            }
        },
        ACTION_NAMES,
    )
    assert rules[100] == [ActionSpec("github_issue", {"repo": "o/r"}), ActionSpec("kanban_card", {"board": "b"})]
    assert rules[200] == [ActionSpec("github_discussion", {"repo": "o/r"})]


@pytest.mark.parametrize(
    "data",
    [
        None,
        {"channels": []},
        {"channels": {"abc": [{"action": "github_issue"}]}},
        {"channels": {"1": []}},
        {"channels": {"1": [{"repo": "o/r"}]}},
        {"channels": {"1": [{"action": "send_email"}]}},
    ],
)
def test_invalid_rules_are_rejected(data):
    with pytest.raises(RulesError):
        parse_rules(data, ACTION_NAMES)


def test_legacy_env_keeps_working():
    rules = legacy_rules(
        {"FORUM_CHANNEL_ID": "1", "DISCUSSION_CHANNEL_ID": "2", "GITHUB_REPO_OWNER": "o", "GITHUB_REPO_NAME": "r"}
    )
    assert rules[1][0].action == "github_issue" and rules[1][0].options["repo"] == "o/r"
    assert rules[2][0].action == "github_discussion"


def _touch(path, offset):
    os.utime(path, (time.time() + offset, time.time() + offset))


def test_store_reloads_on_change_and_keeps_rules_when_invalid(tmp_path):
    path = tmp_path / "rules.yaml"
    path.write_text(RULE_ONE, encoding="utf-8")
    store = RulesStore(path, ACTION_NAMES, env={})
    assert list(store.get()) == [1]

    path.write_text(RULE_TWO, encoding="utf-8")
    _touch(path, 5)
    assert list(store.get()) == [2]

    path.write_text("channels: [broken", encoding="utf-8")
    _touch(path, 10)
    assert list(store.get()) == [2]


def test_store_without_file_uses_legacy_env(tmp_path):
    env = {"FORUM_CHANNEL_ID": "7", "GITHUB_REPO_OWNER": "o", "GITHUB_REPO_NAME": "r"}
    store = RulesStore(tmp_path / "missing.yaml", ACTION_NAMES, env=env)
    assert list(store.get()) == [7]
