"""
Tests for PR-feedback subcommand
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dev_lifecycle.extensions.pr_feedback import (
    fetch_unresolved_threads,
    classify_feedback,
    reply_to_thread,
    resolve_thread
)


class TestPRFeedback(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_fetch_unresolved_threads(self, mock_run):
        """Test fetching unresolved PR feedback threads"""
        mock_response = json.dumps({
            "data": [
                {
                    "id": 1,
                    "state": "OPEN",
                    "path": "src/index.js",
                    "line": 10,
                    "comments": [
                        {
                            "id": 101,
                            "body": "Fix this bug",
                            "author": {"login": "reviewer1"}
                        }
                    ]
                }
            ]
        })
        
        # Mock gh api to return JSON
        with patch('dev_lifecycle.extensions.pr_feedback.subprocess.run') as mock:
            mock.return_value.stdout = mock_response
            mock.return_value.returncode = 0
            
            threads = fetch_unresolved_threads(123, "user/repo")
            
            mock.assert_called_once_with([
                "gh", "api", 
                "repos/user/repo/pulls/123/review_threads?per_page=100"
            ], capture_output=True, text=True, check=True)
            self.assertEqual(len(threads), 1)
            self.assertEqual(threads[0]["id"], 1)
    
    @patch('subprocess.run')
    def test_classify_feedback_apply(self, mock_run):
        """Test classifying feedback as apply"""
        # Read the file and surrounding code
        with patch('builtins.open', mock_open(read_data="const x = 1\n// TODO: fix this\n")):
            result = classify_feedback(
                path="src/index.js",
                line=10,
                feedback_body="Fix this bug"
            )
            self.assertEqual(result, "apply")
    
    @patch('subprocess.run')
    def test_reply_to_thread_correct_thread(self, mock_run):
        """Test replying to feedback on the correct thread"""
        mock_run.return_value.returncode = 0
        
        # Mock reading file + surrounding code to determine fix
        with patch('builtins.open', mock_open(read_data="const x = 1\n// TODO: fix this\n")):
            with patch('dev_lifecycle.extensions.pr_feedback.run_tests'):
                reply = reply_to_thread(
                    pr_number=123,
                    thread_id=1,
                    comment_id=101,
                    feedback_body="Fix this bug",
                    classification="apply",
                    fix_description="changed X; tests pass"
                )
        
        # Verify reply is posted to correct comment
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        # The body should reference the fix and include test results
        body_arg = args[0]  # First positional arg should be the body
        self.assertIn("Fixed:", body_arg)
        self.assertIn("tests pass", body_arg)
        # Should include in_reply_to=101
        self.assertIn("in_reply_to=101", str(args))
    
    @patch('subprocess.run')
    def test_resolve_thread(self, mock_run):
        """Test resolving a feedback thread"""
        mock_run.return_value.returncode = 0
        
        result = resolve_thread(
            pr_number=123,
            thread_id=1
        )
        
        mock_run.assert_called_once_with([
            "gh", "api", "-X", "PATCH",
            "repos/user/repo/pulls/123/review_threads/1",
            "-f", "resolved=true"
        ], capture_output=True, text=True, check=True)
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()