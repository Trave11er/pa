#!/usr/bin/env bash
# Claude Code status line: model name and how full the context window is.
# Claude Code pipes session JSON on stdin; jq isn't installed here, so parse with python3.
exec python3 -c '
import json, sys

data = json.load(sys.stdin)
model = data.get("model", {}).get("display_name", "?")
ctx = data.get("context_window") or {}
usage = ctx.get("current_usage") or {}
used = sum(usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
pct = 100 * used / 200_000  # fixed 200K budget, regardless of the model window
filled = min(10, round(pct / 10))
color = "\033[32m" if pct < 50 else "\033[33m" if pct < 80 else "\033[31m"
bar = "\u2588" * filled + "\u2591" * (10 - filled)
print(f"{model} | ctx {color}{bar} {pct:.0f}% of 200K ({used / 1000:.0f}K)\033[0m")
'
