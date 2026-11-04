# Personal assistants

A collection of subprojects, one per top-level directory. Each has its own README, `AGENTS.md`, skills (`.claude/skills/`), and the same layout: `core/`, `connectors/`, `tests/`, `data/` and `notes/` (both git-ignored).

| Subproject | What it does |
|------------|--------------|
| [food/](food/README.md) | Grocery tracker: reads a Notion to-do list, predicts what to buy next. |
| [coach/](coach/README.md) | Training log: syncs Garmin sessions, reports fitness, fatigue and form. |

Each subproject's vocabulary is in its `GLOSSARY.md`.

Shared at the root: `.devcontainer/`, `pyproject.toml` (lint config and pins), `lint.sh`, `.claude/settings.json`, `AGENTS.md`. Run everything from the root: `python3 -m pytest -q`, `./lint.sh`.

The devcontainer's base image comes from `DEVCONTAINER_IMAGE` in `.devcontainer/.env` (git-ignored), defaulting to `mcr.microsoft.com/devcontainers/python:3.12`. To run agents headless in it, see [.devcontainer/README.md](.devcontainer/README.md).

## Syncing with a remote host

`./remote.sh user@host push|pull code|data|notes|env` syncs with the copy of this repo at `~/pa` on the remote.

- `code` uses git on the current branch: `push` runs `git push --force`, which overwrites the remote branch, `pull` runs `git pull --ff-only`. Only committed work travels. Before your first push, run this once on the remote: `git -C ~/pa config receive.denyCurrentBranch updateInstead`.
- `data` and `notes` use rsync with `--delete` across every subproject's `data/` or `notes/` folder. If a sync would delete anything, the script lists the files and asks before going ahead. rsync must be installed on both machines.
- `env` uses rsync on each top-level folder's `.env` (e.g. `food/.env`, `.devcontainer/.env`), without `--delete`. If a sync would overwrite an existing `.env`, the script lists the files and asks before going ahead. `code`, `data` and `notes` never carry `.env` files.
