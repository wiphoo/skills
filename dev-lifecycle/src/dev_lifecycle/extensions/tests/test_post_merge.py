"""Tests for the post-merge extension."""

import json
import os
import unittest
from unittest.mock import patch

from dev_lifecycle.extensions.post_merge import PostMergeHandler

JIRA_ENV = {
    "JIRA_BASE_URL": "https://test.atlassian.net",
    "JIRA_API_TOKEN": "tok",
    "JIRA_USER_EMAIL": "me@test.com",
}


class TestPostMerge(unittest.TestCase):

    def setUp(self):
        self.h = PostMergeHandler("user/repo")

    @patch("subprocess.run")
    def test_confirm_merge_uses_supported_fields(self, mock_run):
        mock_run.return_value.stdout = '{"mergedAt": "2026-01-01T00:00:00Z", "baseRefName": "main"}'
        self.assertTrue(self.h.confirm_merge("github", 456))
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[:5], ["gh", "pr", "view", "456", "--repo"])
        self.assertIn("mergedAt,baseRefName", cmd)

    @patch("subprocess.run")
    def test_confirm_merge_not_merged(self, mock_run):
        mock_run.return_value.stdout = '{"mergedAt": null, "baseRefName": "main"}'
        self.assertFalse(self.h.confirm_merge("github", 456))

    @patch("subprocess.run")
    def test_detect_issue_github(self, mock_run):
        mock_run.return_value.stdout = '{"closingIssuesReferences": [{"number": 42}]}'
        self.assertEqual(self.h.detect_issue_github(456), 42)

    @patch("subprocess.run")
    def test_detect_issue_jira_from_branch_title_body(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"headRefName": "feat/x", "title": "Add thing", "body": "Closes PROJ-123"})
        self.assertEqual(self.h.detect_issue_jira(456), "PROJ-123")

    @patch("subprocess.run")
    def test_detect_issue_jira_none(self, mock_run):
        mock_run.return_value.stdout = '{"headRefName": "x", "title": "t", "body": null}'
        self.assertIsNone(self.h.detect_issue_jira(456))

    @patch.dict(os.environ, JIRA_ENV)
    @patch("subprocess.run")
    def test_update_jira_issue_sends_adf_and_fails_on_http_error(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.h.update_jira_issue("PROJ-456", "merged"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("--fail-with-body", cmd)
        self.assertIn("https://test.atlassian.net/rest/api/3/issue/PROJ-456/comment", cmd)
        self.assertEqual(json.loads(cmd[cmd.index("-d") + 1])["body"]["type"], "doc")

    @patch("subprocess.run")
    def test_sync_branch_runs_two_commands(self, mock_run):
        self.assertTrue(self.h.sync_branch("main"))
        self.assertEqual([c.args[0] for c in mock_run.call_args_list],
                         [["git", "switch", "main"], ["git", "pull", "--ff-only"]])


if __name__ == "__main__":
    unittest.main()
