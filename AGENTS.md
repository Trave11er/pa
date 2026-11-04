# Agent guidelines

This repo is a collection of subprojects, one per top-level directory (e.g. `food/`), each with its own `AGENTS.md`. Run every command from the repo root.

- Every function gets a docstring of at least one line explaining why it exists, not what it does. The docstring must be shorter than the body (body at least 2x as many lines as the docstring), unless the function is a stub whose body is only its docstring.
- Name functions and methods after what they do, using the same verb/noun as their docstring (e.g. `fetch_boxes` → "Fetch every checkbox…"), so the name alone predicts the docstring.
- Prefix module-level functions, classes and constants with `_` when nothing outside their module, apart from its own unit tests, uses them; CLI entry points like `main` stay public.
- Run the tests after every change: `python3 -m pytest -q` (covers every subproject).
- Run `./lint.sh` after every change (ruff, flake8, basedpyright; config in `pyproject.toml`) and fix what it reports.
