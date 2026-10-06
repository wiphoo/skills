"""Tests for the task-coding extension."""

import json
import os
import unittest
from unittest.mock import patch

from dev_lifecycle.extensions.task_coding import GitHubTaskCoding, JiraTaskCoding

JIRA_ENV = {
    "JIRA_BASE_URL": "https://company.atlassian.net",
    "JIRA_API_TOKEN": "test-token",
    "JIRA_USER_EMAIL": "user@company.com",
}


class TestTaskCoding(unittest.TestCase):

    def test_github_plan_and_execute(self):
        tc = GitHubTaskCoding()
        plan_id = tc.create_plan("github", "123")
        self.assertEqual(plan_id, "plan-github-123")
        self.assertTrue(tc.execute_plan(plan_id))

    def test_jira_plan_and_branch(self):
        tc = JiraTaskCoding()
        self.assertEqual(tc.create_plan("jira", "PROJ-1"), "plan-jira-PROJ-1")
        self.assertEqual(tc.create_branch("PROJ-1"), "task/PROJ-1")

    @patch.dict(os.environ, JIRA_ENV)
    @patch("subprocess.run")
    def test_jira_link_pr_posts_to_comment_endpoint(self, mock_run):
        JiraTaskCoding().link_pr("PROJ-1", "https://github.com/u/r/pull/2")
        cmd = mock_run.call_args[0][0]
        self.assertIn("https://company.atlassian.net/rest/api/3/issue/PROJ-1/comment", cmd)
        self.assertEqual(cmd[cmd.index("-u") + 1], "user@company.com:test-token")
        self.assertIn("body", json.loads(cmd[cmd.index("-d") + 1]))


if __name__ == "__main__":
    unittest.main()
