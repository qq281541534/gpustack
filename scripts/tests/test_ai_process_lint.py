import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_process_lint import lint  # noqa: E402

LIGHT_BODY = "## 修改\n\n改了 README。\n\n## 验证\n\n渲染检查。\n"
RUNTIME_BODY = (
    "Refs #12\n\n## 修改\n\nx\n\n## 验证\n\nx\n\n## 发布影响\n\nx\n\n"
    "## 上游冲突风险\n\nx\n\n## 回滚\n\nx\n"
)


class LintTest(unittest.TestCase):
    def test_docs_pr_without_issue_passes(self):
        self.assertEqual(lint(LIGHT_BODY, "dev", "dev", "docs-only"), [])

    def test_process_pr_without_issue_passes(self):
        self.assertEqual(lint(LIGHT_BODY, "dev", "dev", "process-only"), [])

    def test_runtime_pr_requires_issue_and_sections(self):
        errors = lint(LIGHT_BODY, "dev", "dev", "runtime")
        self.assertTrue(any("Refs" in e for e in errors))
        self.assertTrue(any("回滚" in e for e in errors))

    def test_runtime_pr_with_issue_passes(self):
        self.assertEqual(lint(RUNTIME_BODY, "dev", "dev", "runtime"), [])

    def test_legacy_section_names_accepted(self):
        body = RUNTIME_BODY.replace("## 修改", "## 摘要").replace(
            "## 发布影响", "## 部署影响"
        )
        self.assertEqual(lint(body, "dev", "dev", "runtime"), [])

    def test_unknown_scope_treated_as_runtime(self):
        errors = lint(LIGHT_BODY, "dev", "dev", "unknown")
        self.assertTrue(any("Refs" in e for e in errors))

    def test_auto_close_keywords_rejected(self):
        for keyword in ("Closes", "fixes", "Resolved", "close"):
            with self.subTest(keyword=keyword):
                body = f"{keyword} #3\n\n{LIGHT_BODY}"
                errors = lint(body, "dev", "dev", "docs-only")
                self.assertTrue(any("auto-close" in e for e in errors))

    def test_wrong_base_branch_rejected(self):
        errors = lint(LIGHT_BODY, "main", "dev", "docs-only")
        self.assertTrue(any("base branch" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
