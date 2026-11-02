---
id: TASK-6
title: Replace aadiscordbot in our plugins with the router
status: To Do
assignee: []
created_date: '2026-11-02 13:18'
labels: []
dependencies: []
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Decision 6 in doc-1: our own router replaces aadiscordbot. Inventory what aa-kanban (and other plugins) use from aadiscordbot - DMs, ticket thread creation, thread-to-comment sync, message command - and design how the router takes these over. Until then aadiscordbot is tolerated (AGENTS 15).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Inventory of aadiscordbot usage per plugin
- [ ] #2 Design for each function in the router, as a follow-up proposal
<!-- AC:END -->
