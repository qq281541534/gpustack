#!/usr/bin/env python3
"""Classify changed files into AI Issue-to-Production delivery scopes.

Single source of truth for both the PR check and the post-merge image build,
so the two never disagree on whether a change needs an Issue or a new image.

Scopes (ordered by impact; a mixed change takes the highest):
  docs-only           ordinary docs, not consumed by the product or release
  process-only        agent rules, templates, process lint/tests
  release-governance  workflows, deploy scripts, production compose files
  runtime             product source, dependencies, image inputs, tests
  unknown             unmapped paths; treated like runtime and built
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from pathlib import Path

SCOPE_ORDER = [
    "docs-only",
    "process-only",
    "release-governance",
    "runtime",
    "unknown",
]

# First match wins, so product paths come before generic doc globs
# (e.g. a Markdown file under gpustack/ stays runtime).
# Each rule: (glob, scope, is_image_input).
RULES: list[tuple[str, str, bool]] = [
    # Docker build context of pack/Dockerfile.
    ("gpustack/**", "runtime", True),
    ("pack/**", "runtime", True),
    ("hack/**", "runtime", True),
    ("static/**", "runtime", True),
    ("docker-compose/grafana/**", "runtime", True),
    ("Makefile", "runtime", True),
    ("pyproject.toml", "runtime", True),
    ("uv.lock", "runtime", True),
    ("requirements*.txt", "runtime", True),
    ("setup.py", "runtime", True),
    ("setup.cfg", "runtime", True),
    ("alembic.ini", "runtime", True),
    (".dockerignore", "runtime", True),
    # Product tests: need app checks but are excluded from the image.
    ("tests/**", "runtime", False),
    ("conftest.py", "runtime", False),
    ("pytest.ini", "runtime", False),
    # Release governance: may change how we deploy, never needs a new image.
    (".github/workflows/**", "release-governance", False),
    ("scripts/deploy-images.sh", "release-governance", False),
    ("scripts/verify_image_build_source.py", "release-governance", False),
    ("docker-compose/**", "release-governance", False),
    ("charts/**", "release-governance", False),
    # Process: agent rules, templates, process lint and its tests.
    ("AGENTS.md", "process-only", False),
    ("CLAUDE.md", "process-only", False),
    (".claude/**", "process-only", False),
    (".trae/**", "process-only", False),
    (".cursor/**", "process-only", False),
    (".gemini/**", "process-only", False),
    ("skills/**", "process-only", False),
    (".github/ISSUE_TEMPLATE/**", "process-only", False),
    (".github/pull_request_template.md", "process-only", False),
    (".github/labeler.yml", "process-only", False),
    (".github/labeler.yaml", "process-only", False),
    (".github/**", "release-governance", False),
    ("scripts/ai_process_lint.py", "process-only", False),
    ("scripts/classify_change_scope.py", "process-only", False),
    ("scripts/tests/**", "process-only", False),
    (".pre-commit-config.yaml", "process-only", False),
    (".flake8", "process-only", False),
    (".gitignore", "process-only", False),
    (".gitattributes", "process-only", False),
    # Ordinary docs (upstream product docs site is not published by this fork).
    ("docs/**", "docs-only", False),
    ("lmzj-docs/**", "docs-only", False),
    ("mkdocs.yml", "docs-only", False),
    ("README*", "docs-only", False),
    ("LICENSE", "docs-only", False),
    ("*.md", "docs-only", False),
    ("*.mdx", "docs-only", False),
    ("*.png", "docs-only", False),
    ("*.jpg", "docs-only", False),
    ("*.gif", "docs-only", False),
]


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    if "/" in pattern:
        return fnmatch.fnmatchcase(path, pattern)
    # Bare patterns match the basename anywhere in the tree.
    return fnmatch.fnmatchcase(path.rsplit("/", 1)[-1], pattern)


def classify_file(path: str) -> tuple[str, bool]:
    for pattern, scope, image_input in RULES:
        if _matches(path, pattern):
            return scope, image_input
    return "unknown", True


def classify(files: list[str]) -> dict:
    files = sorted({f.strip() for f in files if f.strip()})
    if not files:
        # No evidence of what changed: be conservative.
        return {
            "scope": "unknown",
            "needs_issue": True,
            "needs_app_check": True,
            "needs_build": True,
            "files": {},
        }

    per_file = {}
    needs_build = False
    for path in files:
        scope, image_input = classify_file(path)
        per_file[path] = scope
        needs_build = needs_build or image_input

    scope = max(per_file.values(), key=SCOPE_ORDER.index)
    runtime_like = scope in ("runtime", "unknown")
    return {
        "scope": scope,
        "needs_issue": runtime_like,
        "needs_app_check": runtime_like,
        "needs_build": needs_build,
        "files": per_file,
    }


def git_changed_files(base: str, head: str) -> list[str] | None:
    if not base or set(base) == {"0"}:
        return None
    result = subprocess.run(
        ["git", "diff", "--name-only", "--no-renames", base, head],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def write_github_output(result: dict) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"scope={result['scope']}\n")
        for key in ("needs_issue", "needs_app_check", "needs_build"):
            handle.write(f"{key}={str(result[key]).lower()}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--files-from", help="File with one path per line; - for stdin")
    source.add_argument("--base", help="Git base revision; diff base..--head")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args()

    if args.files_from is not None:
        text = (
            sys.stdin.read()
            if args.files_from == "-"
            else Path(args.files_from).read_text(encoding="utf-8")
        )
        files = text.splitlines()
    else:
        files = git_changed_files(args.base, args.head)
        if files is None:
            print("No usable base revision; classifying conservatively.")
            files = []

    result = classify(files)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.github_output:
        write_github_output(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
