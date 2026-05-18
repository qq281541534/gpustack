#!/usr/bin/env python3
"""Verify a production image SHA comes from a merged PR to the release branch."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request


FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def github_get(url: str, token: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gpustack-ai-release-check",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--base-branch", default="dev")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    args = parser.parse_args()

    sha = args.sha.strip().lower()
    if not FULL_SHA_RE.fullmatch(sha):
        print("Image build SHA must be a full 40-character lowercase git SHA.", file=sys.stderr)
        return 1

    if not args.repo:
        print("GITHUB_REPOSITORY is required.", file=sys.stderr)
        return 1
    if not args.token:
        print("GITHUB_TOKEN is required.", file=sys.stderr)
        return 1

    url = f"https://api.github.com/repos/{args.repo}/commits/{sha}/pulls"
    try:
        pulls = github_get(url, args.token)
    except urllib.error.HTTPError as exc:
        print(f"GitHub API request failed: HTTP {exc.code}", file=sys.stderr)
        return 1

    if not isinstance(pulls, list):
        print("Unexpected GitHub API response while checking associated PRs.", file=sys.stderr)
        return 1

    for pull in pulls:
        if not isinstance(pull, dict):
            continue
        base = pull.get("base") or {}
        if (
            base.get("ref") == args.base_branch
            and pull.get("merged_at")
            and pull.get("state") == "closed"
        ):
            number = pull.get("number")
            print(f"SHA {sha} is associated with merged PR #{number} into {args.base_branch}.")
            return 0

    print(
        f"SHA {sha} is not associated with a merged PR into {args.base_branch}; "
        "refusing production image build.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
