"""Tests for the PR-feedback extension."""

import json
import unittest
from unittest.mock import patch

from dev_lifecycle.extensions.pr_feedback import PRFeedbackHandler

THREADS = {"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [
    {"id": "PRRT_open", "isResolved": False, "comments": {"nodes": [
        {"databaseId": 101, "body": "Fix this bug", "path": "a.py", "line": 3,
         "author": {"login": "reviewer"}}]}},
    {"id": "PRRT_done", "isResolved": True, "comments": {"nodes": []}},
]}}}}}


class TestPRFeedback(unittest.TestCase):

    def setUp(self):
        self.h = PRFeedbackHandler("user/repo")

    @patch("subprocess.run")
    def test_fetch_unresolved_uses_graphql(self, mock_run):
        mock_run.return_value.stdout = json.dumps(THREADS)
        threads = self.h.fetch_unresolved_threads(123)
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[:3], ["gh", "api", "graphql"])
        self.assertIn("owner=user", cmd)
        self.assertIn("name=repo", cmd)
        self.assertIn("number=123", cmd)
        self.assertEqual([t["id"] for t in threads], ["PRRT_open"])

    def test_classify_feedback(self):
        self.assertEqual(self.h.classify_feedback("a.py", 1, "Fix this bug"), "apply")
        self.assertEqual(self.h.classify_feedback("a.py", 1, "rename for taste"), "pushback")

    @patch("subprocess.run")
    def test_reply_targets_comment_replies_endpoint(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.h.reply_to_thread(123, 101, "Fix this bug", "apply", "changed X"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("repos/user/repo/pulls/123/comments/101/replies", cmd)
        self.assertIn("body=Fixed: changed X", cmd)

    @patch("subprocess.run")
    def test_resolve_thread_uses_graphql_node_id(self, mock_run):
        mock_run.return_value.returncode = 0
        self.assertTrue(self.h.resolve_thread("PRRT_open"))
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[:3], ["gh", "api", "graphql"])
        self.assertIn("id=PRRT_open", cmd)


if __name__ == "__main__":
    unittest.main()
