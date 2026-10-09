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
        self.assertEqual(self.h.detect_issue_github(456), ("user/repo", 42))  # no repo info -> PR's repo

    @patch("subprocess.run")
    def test_detect_issue_github_rejects_multiple_closing_issues(self, mock_run):
        mock_run.return_value.stdout = '{"closingIssuesReferences": [{"number": 42}, {"number": 7}]}'
        with self.assertRaises(ValueError):
            self.h.detect_issue_github(456)

    @patch("subprocess.run")
    def test_detect_issue_github_falls_back_to_title_body_reference(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"closingIssuesReferences": [], "title": "Add thing", "body": "Related #42"})
        self.assertEqual(self.h.detect_issue_github(456), ("user/repo", 42))

    @patch("subprocess.run")
    def test_detect_issue_github_fallback_rejects_multiple_and_none(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"closingIssuesReferences": [], "title": "Related #10", "body": "Fixes #20"})
        with self.assertRaises(ValueError):
            self.h.detect_issue_github(456)
        mock_run.return_value.stdout = json.dumps(
            {"closingIssuesReferences": [], "title": "nothing", "body": None})
        self.assertIsNone(self.h.detect_issue_github(456))

    @patch("subprocess.run")
    def test_detect_issue_github_closing_reference_wins_over_mentions(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"closingIssuesReferences": [{"number": 7}], "title": "Related #10", "body": "x"})
        self.assertEqual(self.h.detect_issue_github(456), ("user/repo", 7))

    @patch("subprocess.run")
    def test_detect_issue_github_keeps_cross_repo_closing_reference(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [
            {"number": 42, "url": "https://github.com/owner/other-repo/issues/42"}]})
        self.assertEqual(self.h.detect_issue_github(456), ("owner/other-repo", 42))

    @patch("subprocess.run")
    def test_detect_issue_github_same_number_in_two_repos_is_ambiguous(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [
            {"number": 42, "url": "https://github.com/user/repo/issues/42"},
            {"number": 42, "url": "https://github.com/owner/other-repo/issues/42"}]})
        with self.assertRaises(ValueError):
            self.h.detect_issue_github(456)

    @patch("subprocess.run")
    def test_detect_issue_github_fallback_keeps_qualified_mention(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"closingIssuesReferences": [], "title": "t", "body": "Fixes owner/other-repo#42"})
        self.assertEqual(self.h.detect_issue_github(456), ("owner/other-repo", 42))

    @patch("subprocess.run")
    def test_detect_issue_github_fallback_parses_full_issue_url(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [], "title": "t",
            "body": "See https://github.com/acme/other/issues/42#issuecomment-1 for context"})
        self.assertEqual(self.h.detect_issue_github(456), ("acme/other", 42))

    @patch("subprocess.run")
    def test_detect_issue_github_url_and_matching_qualified_ref_are_one_issue(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [], "title": "acme/other#42",
            "body": "https://github.com/acme/other/issues/42"})
        self.assertEqual(self.h.detect_issue_github(456), ("acme/other", 42))

    @patch("subprocess.run")
    def test_detect_issue_github_url_and_different_ref_is_ambiguous(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [], "title": "Related #7",
            "body": "https://github.com/acme/other/issues/42"})
        with self.assertRaises(ValueError):
            self.h.detect_issue_github(456)

    @patch("subprocess.run")
    def test_detect_issue_github_pull_request_url_is_not_an_issue(self, mock_run):
        mock_run.return_value.stdout = json.dumps({"closingIssuesReferences": [], "title": "t",
            "body": "Follows https://github.com/acme/other/pull/9"})
        self.assertIsNone(self.h.detect_issue_github(456))

    @patch("subprocess.run")
    def test_update_github_issue_targets_given_repo(self, mock_run):
        mock_run.return_value.returncode = 0
        self.h.update_github_issue(42, "merged", repo="owner/other-repo")
        self.assertIn("repos/owner/other-repo/issues/42/comments", mock_run.call_args[0][0])
        self.h.update_github_issue(42, "merged")
        self.assertIn("repos/user/repo/issues/42/comments", mock_run.call_args[0][0])

    @patch("subprocess.run")
    def test_detect_issue_jira_rejects_multiple_keys(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"headRefName": "PROJ-1/x", "title": "t", "body": "also PROJ-2"})
        with self.assertRaises(ValueError):
            self.h.detect_issue_jira(456)

    @patch("subprocess.run")
    def test_detect_issue_jira_same_key_repeated_is_not_ambiguous(self, mock_run):
        mock_run.return_value.stdout = json.dumps(
            {"headRefName": "PROJ-1/x", "title": "PROJ-1 fix", "body": "PROJ-1"})
        self.assertEqual(self.h.detect_issue_jira(456), "PROJ-1")

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
    def test_sync_branch_switches_then_pulls_when_clean(self, mock_run):
        mock_run.return_value.stdout = ""
        self.assertTrue(self.h.sync_branch("main"))
        self.assertEqual([c.args[0] for c in mock_run.call_args_list],
                         [["git", "status", "--porcelain"],
                          ["git", "switch", "main"], ["git", "pull", "--ff-only"]])

    @patch("subprocess.run")
    def test_sync_branch_refuses_dirty_worktree(self, mock_run):
        mock_run.return_value.stdout = " M file.py\n"
        with self.assertRaises(RuntimeError):
            self.h.sync_branch("main")
        self.assertEqual(mock_run.call_count, 1)  # never switched


if __name__ == "__main__":
    unittest.main()
