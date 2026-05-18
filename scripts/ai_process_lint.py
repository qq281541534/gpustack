#!/usr/bin/env python3
"""Validate PR process requirements for AI Issue-to-Production."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


AUTO_CLOSE_RE = re.compile(r"\b(closes|fixes|resolves)\s+#\d+", re.IGNORECASE)
REFS_RE = re.compile(r"\bRefs\s+#\d+\b")


def load_pr_body(event_path: str | None, body_file: str | None, body: str | None) -> tuple[str, str]:
    if body is not None:
        return body, ""
    if body_file is not None:
        return Path(body_file).read_text(encoding="utf-8"), ""
    if event_path is None:
        return "", ""

    event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    pull_request = event.get("pull_request") or {}
    return pull_request.get("body") or "", (pull_request.get("base") or {}).get("ref") or ""


def contains_section(body: str, names: list[str]) -> bool:
    for name in names:
        if re.search(rf"^##\s+{re.escape(name)}\s*$", body, flags=re.MULTILINE):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", default=None)
    parser.add_argument("--body-file", default=None)
    parser.add_argument("--body", default=None)
    parser.add_argument("--target-branch", default="dev")
    args = parser.parse_args()

    body, base_branch = load_pr_body(args.event_path, args.body_file, args.body)
    errors: list[str] = []

    if base_branch and base_branch != args.target_branch:
        errors.append(f"PR base branch must be {args.target_branch!r}, got {base_branch!r}.")

    if not REFS_RE.search(body):
        errors.append("PR body must contain `Refs #<issue-number>`.")

    if AUTO_CLOSE_RE.search(body):
        errors.append("PR body must not use auto-close keywords: Closes, Fixes, Resolves.")

    required_sections = [
        ["摘要", "Summary"],
        ["验证", "Validation"],
        ["部署影响", "Deployment Impact"],
        ["回滚", "Rollback"],
        ["上游冲突风险", "Upstream Conflict Risk"],
    ]
    for names in required_sections:
        if not contains_section(body, names):
            errors.append(f"PR body missing section: {' / '.join(names)}.")

    if errors:
        print("AI Issue-to-Production PR process lint failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("AI Issue-to-Production PR process lint passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
