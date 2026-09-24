#!/usr/bin/env python3
"""Validate PR process requirements for AI Issue-to-Production.

Requirements depend on the change scope from classify_change_scope.py:
ordinary docs and simple process changes need no Issue; runtime and
unknown changes must reference an Issue and describe release impact.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

AUTO_CLOSE_RE = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+#\d+", re.I)
REFS_RE = re.compile(r"\bRefs\s+#\d+\b")

LIGHT_SECTIONS = [
    ["修改", "摘要", "Summary"],
    ["验证", "Validation"],
]
RUNTIME_SECTIONS = LIGHT_SECTIONS + [
    ["发布影响", "部署影响", "Deployment Impact"],
    ["上游冲突风险", "Upstream Conflict Risk"],
    ["回滚", "Rollback"],
]
RUNTIME_SCOPES = {"runtime", "unknown"}


def fetch_live_pr(repo: str, number: str, token: str) -> dict:
    """Read current PR metadata so re-runs see edits, not the old payload."""
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{number}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gpustack-ai-process-lint",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_pr(args: argparse.Namespace) -> tuple[str, str]:
    if args.body is not None:
        return args.body, ""
    if args.body_file is not None:
        return Path(args.body_file).read_text(encoding="utf-8"), ""
    if args.pr_number and args.repo and args.token:
        pull_request = fetch_live_pr(args.repo, args.pr_number, args.token)
    elif args.event_path is not None:
        event = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        pull_request = event.get("pull_request") or {}
    else:
        return "", ""
    base = (pull_request.get("base") or {}).get("ref") or ""
    return pull_request.get("body") or "", base


def contains_section(body: str, names: list[str]) -> bool:
    return any(
        re.search(rf"^##\s+{re.escape(name)}\s*$", body, flags=re.MULTILINE)
        for name in names
    )


def lint(body: str, base_branch: str, target_branch: str, scope: str) -> list[str]:
    errors: list[str] = []

    if base_branch and base_branch != target_branch:
        errors.append(f"PR base branch must be {target_branch!r}, got {base_branch!r}.")

    if AUTO_CLOSE_RE.search(body):
        errors.append(
            "PR body must not use auto-close keywords (Closes/Fixes/Resolves); "
            "use `Refs #<issue>`."
        )

    runtime_like = scope in RUNTIME_SCOPES
    if runtime_like and not REFS_RE.search(body):
        errors.append(
            f"Scope {scope!r} requires `Refs #<issue-number>` in the PR body."
        )

    for names in RUNTIME_SECTIONS if runtime_like else LIGHT_SECTIONS:
        if not contains_section(body, names):
            errors.append(f"PR body missing section: {' / '.join(names)}.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", default=None)
    parser.add_argument("--body-file", default=None)
    parser.add_argument("--body", default=None)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--pr-number", default=None)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--target-branch", default="dev")
    parser.add_argument(
        "--scope",
        default="unknown",
        choices=[
            "docs-only",
            "process-only",
            "release-governance",
            "runtime",
            "unknown",
        ],
    )
    args = parser.parse_args()

    body, base_branch = load_pr(args)
    errors = lint(body, base_branch, args.target_branch, args.scope)

    if errors:
        print(
            f"AI Issue-to-Production PR process lint failed (scope={args.scope}):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"AI Issue-to-Production PR process lint passed (scope={args.scope}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
