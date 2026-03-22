# Personal assistants

A collection of subprojects, one per top-level directory. Each has its own README, `AGENTS.md`, skills (`.claude/skills/`), and the same layout: `core/`, `connectors/`, `tests/`, `data/` and `notes/` (both git-ignored).

| Subproject | What it does |
|------------|--------------|
| [food/](food/README.md) | Grocery tracker: reads a Notion to-do list, predicts what to buy next. |

Shared at the root: `.devcontainer/`, `pyproject.toml` (lint config and pins), `lint.sh`, `.claude/settings.json`, `AGENTS.md`. Run everything from the root: `python3 -m pytest -q`, `./lint.sh`.

The devcontainer's image comes from `DEVCONTAINER_IMAGE` in `.devcontainer/.env` (git-ignored), defaulting to `mcr.microsoft.com/devcontainers/python:3.12`.
