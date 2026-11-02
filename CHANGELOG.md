# Changelog

## [0.2.0] - 2026-11-02

### Added

- **Rule engine (TASK-3):** `rules.yaml` maps each Discord channel to one or more actions.
  - The file is reread when it changes, with no restart needed.
  - An invalid file is logged, and the previous rules stay in force.
- **Kanban card action (TASK-4):** `kanban_card` creates a card on an aa-kanban board through its intake API, and replies in the thread with a link to the card.
- **Discussion category:** `github_discussion` now uses the category named in `category`.
- **Tests and tooling:** tests with mocked HTTP; `uv`, `ruff` and `mypy`.

### Changed

- The bot is now the `thread_router` package (`python -m thread_router`), replacing `githubBOT.py`. Dependencies moved from `requirements.txt` to `pyproject.toml` / `uv.lock`.
- HTTP calls are async (`httpx`), so they no longer block the bot.
- The starter message is read from the thread id, instead of with a 2-second sleep.
- Threads opened by bots are ignored, and so are repeated events for the same thread.
- **Logging:** INFO by default, and message content no longer appears in the logs. The `on_message` debug dump is gone.
- **Container:** `config/rules.yaml` is mounted into the container.

### Compatibility

- Without `rules.yaml`, the old `.env` keys (`FORUM_CHANNEL_ID`, `DISCUSSION_CHANNEL_ID`, `GITHUB_REPO_OWNER`, `GITHUB_REPO_NAME`) still work.
