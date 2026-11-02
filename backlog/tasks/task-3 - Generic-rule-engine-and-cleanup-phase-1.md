---
id: TASK-3
title: Generic rule engine and cleanup (phase 1)
status: Done
assignee: []
created_date: '2026-11-02 13:18'
updated_date: '2026-11-02 13:56'
labels: []
dependencies: []
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Turn githubBOT.py into a rule-based router (doc-1). Rules in rules.yaml: channel id -> list of actions. Keep GitHub issue/discussion as actions. Async HTTP (httpx), starter message via thread.id, ignore bot-created threads, no DEBUG logging or on_message dump. pytest + ruff via uv. Legacy .env channel ids keep working as fallback.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 rules.yaml maps channels to one or more actions and is reloaded when it changes
- [x] #2 github_issue and github_discussion work as before, discussion category configurable
- [x] #3 Threads opened by bots and channels without a rule are ignored
- [x] #4 No blocking HTTP calls in event handlers; no message content in logs
- [x] #5 pytest covers rule loading, routing and both GitHub actions with mocked HTTP; ruff clean
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Package thread_router: rules.py (rules.yaml, reload on mtime change, legacy .env fallback), actions/ (github_issue, github_discussion, kanban_card), router.py, bot.py. httpx async, starter message via thread id, bot threads and repeated events ignored, INFO logging without content. 19 tests, ruff and mypy clean. Dockerfile on uv, compose mounts ./config.
<!-- SECTION:NOTES:END -->
