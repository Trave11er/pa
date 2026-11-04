#!/usr/bin/env bash
# Move code (via git), or data/notes/.env files (via rsync), between this repo and ~/pa on a remote host.
# .env files travel only with kind env: git doesn't track them and the data/notes syncs exclude them.
set -euo pipefail

usage() {
    echo "usage: $0 user@host push|pull code|data|notes|env" >&2
    exit 1
}

[[ $# -eq 3 ]] || usage
host=$1 direction=$2 kind=$3
[[ $direction == push || $direction == pull ]] || usage
[[ $kind == code || $kind == data || $kind == notes || $kind == env ]] || usage

cd "$(dirname "$0")"
remote="$host:pa"

if [[ $kind == code ]]; then
    branch=$(git rev-parse --abbrev-ref HEAD)
    if [[ $direction == push ]]; then
        git push --force "$remote" "HEAD:$branch" || {
            echo "push rejected; check ~/pa on the remote is a git repo with a clean working tree, and run there once:" >&2
            echo "  git -C ~/pa config receive.denyCurrentBranch updateInstead" >&2
            exit 1
        }
    else
        git pull --ff-only "$remote" "$branch"
    fi
    exit 0
fi

if [[ $direction == push ]]; then
    src=./ dst="$remote/"
else
    src="$remote/" dst=./
fi

if [[ $kind == env ]]; then
    # Each top-level dir's .env; no --delete, so a missing file never removes one.
    opts=(-az --prune-empty-dirs --include='/*/' --include='/*/.env' --exclude='*')
    overwrites=$(rsync "${opts[@]}" --dry-run --itemize-changes "$src" "$dst" | grep -E '^[<>]f' | grep -v '+++++' || true)
    if [[ -n $overwrites ]]; then
        echo "$overwrites"
        read -r -p "Overwrite these existing files on the $direction destination? [y/N] " answer
        [[ $answer == y || $answer == Y ]] || { echo "aborted" >&2; exit 1; }
    fi
    rsync --verbose "${opts[@]}" "$src" "$dst"
    echo "$kind ${direction}ed: $src -> $dst"
    exit 0
fi
# Only <subproject>/<kind>/ is included, so --delete cannot touch anything else.
opts=(-az --delete --exclude='.env*' --include='/*/' --include="/*/$kind/***" --exclude='*')

deletions=$(rsync "${opts[@]}" --dry-run --itemize-changes "$src" "$dst" | grep '^\*deleting' || true)
if [[ -n $deletions ]]; then
    echo "$deletions"
    read -r -p "Delete these files on the $direction destination? [y/N] " answer
    [[ $answer == y || $answer == Y ]] || { echo "aborted" >&2; exit 1; }
fi
rsync --verbose "${opts[@]}" "$src" "$dst"
echo "$kind ${direction}ed: $src -> $dst"
