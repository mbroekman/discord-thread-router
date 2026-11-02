---
id: TASK-4
title: Kanban card action (phase 3)
status: In Progress
assignee: []
created_date: '2026-11-02 13:18'
updated_date: '2026-11-02 13:56'
labels: []
dependencies: []
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Add a kanban_card action that posts the thread to the aa-kanban intake endpoint (KANBAN_BASE_URL, KANBAN_API_KEY) and replies in the thread with the card link. Depends on the aa-kanban intake API.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A thread in a channel with a kanban_card rule creates a card on the configured board and list
- [ ] #2 The bot replies in the thread with a link to the card
- [ ] #3 A failure is reported in the thread and logged, never silent
- [x] #4 Tests with mocked HTTP
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Action and tests done (thread_router/actions/kanban.py). Live test waits for: aa_kanban in APPS_WITH_PUBLIC_VIEWS on the server (user decision), an intake API key, rules.yaml with the 3GODS channel ids, and the container host.
<!-- SECTION:NOTES:END -->
