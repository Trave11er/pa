#!/usr/bin/env bash
# Run ruff, flake8 and basedpyright in the "lint" dependency group; config lives in pyproject.toml.
set -euo pipefail

cd "$(dirname "$0")"

uv run --only-group lint ruff check .
uv run --only-group lint flake8 .
uv run --only-group lint basedpyright .
