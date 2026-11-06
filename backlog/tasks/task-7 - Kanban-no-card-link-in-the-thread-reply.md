---
id: TASK-7
title: 'Kanban: no card link in the thread reply'
status: Done
assignee: []
created_date: '2026-11-06 17:20'
updated_date: '2026-11-06 17:21'
labels: []
dependencies: []
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The reply in the Discord thread includes the card URL. A thread can contain Discord members who have no access to the board, so the link must not be shown. Keep the card number and board name.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The thread reply for a kanban card has no URL
- [x] #2 Card number and board name are still shown
- [x] #3 Tests and docs updated
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
The kanban action returns no URL, so the thread reply shows only the card number and board. Test, README and CHANGELOG updated.
<!-- SECTION:FINAL_SUMMARY:END -->
