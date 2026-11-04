# .devcontainer

Run Claude headless (e.g. on a Pi), from the repo root; set the host path to your checkout:

```bash
docker compose -f .devcontainer/docker-compose.yml build
docker run -d --name pa --restart unless-stopped \
  -w /workspace -v ~/pa:/workspace pa:latest \
  bash -c 'uv sync --group lint
           tmux new-session -d -s claude_food -c /workspace/food "/home/vscode/.local/bin/claude --enable-auto-mode --remote-control food"
           tmux new-session -d -s claude_coach -c /workspace/coach "/home/vscode/.local/bin/claude --enable-auto-mode --remote-control coach"
           sleep infinity'
docker exec -it pa tmux attach -t claude_food   # log in on first attach or when re-login is required
```