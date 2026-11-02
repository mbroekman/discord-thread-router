---
id: TASK-5
title: Rename repository to discord-thread-router
status: In Progress
assignee: []
created_date: '2026-11-02 13:18'
updated_date: '2026-11-02 13:58'
labels: []
dependencies: []
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Rename the GitHub repo and local folder from githubDiscordBOT to discord-thread-router (decision 4 in doc-1). Update README, container name and workspace references.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 GitHub repo renamed, remote updated
- [ ] #2 Local folder, README, docker-compose and workspace docs use the new name
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
GitHub repo renamed to mbroekman/discord-thread-router (old URL redirects); origin updated. Local folder rename failed (folder in use by VS Code/Google Drive): rename plugins/githubDiscordBOT to plugins/discord-thread-router when nothing has it open, then update AGENTS/CLAUDE/GEMINI.md paths and memory. Keep container_name github-discord-bot until the old container is stopped: a new compose project name would start a second bot.
<!-- SECTION:NOTES:END -->
