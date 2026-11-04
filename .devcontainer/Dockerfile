ARG BASE_IMAGE=mcr.microsoft.com/devcontainers/python:3.12
FROM ${BASE_IMAGE}

RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux \
    && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# uv sync fills this venv in the mounted repo at start-up; on PATH, plain python3 uses it
ENV PATH=/workspace/.venv/bin:$PATH

# Claude Code installs into the user's home, so install it as the dev user, not root
USER vscode
RUN curl -fsSL https://claude.ai/install.sh | bash
