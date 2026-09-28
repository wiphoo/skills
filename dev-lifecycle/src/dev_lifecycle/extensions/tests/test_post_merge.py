"""
Tests for post-merge subcommand
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dev_lifecycle.extensions.post_merge import (
    confirm_merge,
    detect_issue_github,
    detect_issue_jira,
    update_github_issue,
    update_jira_issue,
    sync_branch
)


class TestPostMerge(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_confirm_merge_github(self, mock_run):
        mock_run.return_value.stdout = '{"merged": true, "mergeCommit": {"sha": "abc123"}, "baseRef": {"name": "main"}}'
        mock_run.return_value.returncode = 0
        result = confirm_merge("github", 456)
        self.assertTrue(result)
        args, _ = mock_run.call_args
        self.assertIn("gh", args[0])
        self.assertIn("pr", args[0])
        self.assertIn("view", args[0])
        self.assertIn("456", args[0])
    
    @patch('subprocess.run')
    def test_confirm_merge_not_merged(self, mock_run):
        mock_run.return_value.stdout = '{"merged": false}'
        mock_run.return_value.returncode = 0
        with self.assertRaises(Exception) as ctx:
            confirm_merge("github", 456)
        self.assertIn("not merged", str(ctx.exception).lower())
    
    @patch('subprocess.run')
    def test_detect_issue_github(self, mock_run):
        mock_run.return_value.stdout = '{"title": "Fix bug #PROJ-123", "body": "See PROJ-456"}'
        mock_run.return_value.returncode = 0
        result = detect_issue_github(456)
        # Should find PROJ-456 from body
        mock_run.assert_called()
        self.assertIn("PROJ-456", result)
    
    @patch.dict(os.environ, {
        'JIRA_BASE_URL': 'https://test.atlassian.net',
        'JIRA_API_TOKEN': 'test',
        'JIRA_USER_EMAIL': 'test@test.com'
    })
    @patch('subprocess.run')
    def test_update_jira_issue(self, mock_run):
        mock_run.return_value.returncode = 0
        result = update_jira_issue("PROJ-456", "https://github.com/user/repo/pull/456")
        mock_run.assert_called()
        args, _ = mock_run.call_args
        self.assertIn("curl", args[0])
        self.assertIn("POST", args[0])
        self.assertIn("PROJ-456", " ".join(args[0]))
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_sync_branch(self, mock_run):
        mock_run.return_value.returncode = 0
        result = sync_branch("main")
        mock_run.assert_any_call(["git", "switch", "main"], check=True)
        mock_run.assert_any_call(["git", "pull", "--ff-only"], check=True)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()