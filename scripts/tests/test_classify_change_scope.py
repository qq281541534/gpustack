import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from classify_change_scope import classify, classify_file  # noqa: E402


class ClassifyFileTest(unittest.TestCase):
    def test_file_scopes(self):
        cases = {
            "README.md": ("docs-only", False),
            "lmzj-docs/release-log.md": ("docs-only", False),
            "docs/overview.md": ("docs-only", False),
            "AGENTS.md": ("process-only", False),
            ".trae/rules/ai-issue-to-production.md": ("process-only", False),
            ".github/pull_request_template.md": ("process-only", False),
            "scripts/ai_process_lint.py": ("process-only", False),
            ".github/workflows/pr-check.yml": ("release-governance", False),
            "scripts/deploy-images.sh": ("release-governance", False),
            "docker-compose/docker-compose.server.yaml": (
                "release-governance",
                False,
            ),
            # Dashboards are copied into the image by pack/Dockerfile.
            "docker-compose/grafana/grafana_dashboards/a.json": ("runtime", True),
            "gpustack/server/app.py": ("runtime", True),
            # Markdown consumed by the product is not ordinary docs.
            "gpustack/assets/notes.md": ("runtime", True),
            "pack/frontend-ref": ("runtime", True),
            "uv.lock": ("runtime", True),
            "static/catalog_icons/x.png": ("runtime", True),
            "tests/api/test_x.py": ("runtime", False),
            "some/new/thing.bin": ("unknown", True),
        }
        for path, expected in cases.items():
            with self.subTest(path=path):
                self.assertEqual(classify_file(path), expected)


class ClassifyTest(unittest.TestCase):
    def test_docs_only_needs_no_issue_or_build(self):
        result = classify(["README.md", "lmzj-docs/release-log.md"])
        self.assertEqual(result["scope"], "docs-only")
        self.assertFalse(result["needs_issue"])
        self.assertFalse(result["needs_build"])
        self.assertFalse(result["needs_app_check"])

    def test_process_change_needs_no_build(self):
        result = classify(["AGENTS.md", ".github/workflows/build-images.yml"])
        self.assertEqual(result["scope"], "release-governance")
        self.assertFalse(result["needs_issue"])
        self.assertFalse(result["needs_build"])

    def test_mixed_change_takes_highest_scope(self):
        result = classify(["docs/a.md", "gpustack/server/app.py"])
        self.assertEqual(result["scope"], "runtime")
        self.assertTrue(result["needs_issue"])
        self.assertTrue(result["needs_build"])

    def test_tests_only_checked_but_not_built(self):
        result = classify(["tests/api/test_x.py"])
        self.assertEqual(result["scope"], "runtime")
        self.assertTrue(result["needs_app_check"])
        self.assertFalse(result["needs_build"])

    def test_unknown_is_conservative(self):
        result = classify(["docs/a.md", "some/new/thing.bin"])
        self.assertEqual(result["scope"], "unknown")
        self.assertTrue(result["needs_issue"])
        self.assertTrue(result["needs_build"])

    def test_empty_change_list_is_conservative(self):
        result = classify([])
        self.assertEqual(result["scope"], "unknown")
        self.assertTrue(result["needs_build"])


if __name__ == "__main__":
    unittest.main()
