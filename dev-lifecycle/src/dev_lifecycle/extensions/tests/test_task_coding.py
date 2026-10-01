"""
Tests for task coding subcommand
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import sys
import os

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dev_lifecycle.extensions.task_coding import (
    inspect_github_task,
    inspect_jira_task,
    create_worktree,
    generate_plan,
    execute_plan,
    create_pr,
    link_pr_to_tracker,
    cleanup_worktree
)

class TestTaskCoding(unittest.TestCase):
    
    @patch('subprocess.run')
    def test_inspect_github_task(self, mock_run):
        """Test inspecting a GitHub task via gh issue view"""
        mock_run.return_value.stdout = "Task Title\nTask Description\n"
        mock_run.return_value.returncode = 0
        
        result = inspect_github_task(123)
        
        mock_run.assert_called_once_with(
            ["gh", "issue", "view", "123"],
            capture_output=True,
            text=True,
            check=True
        )
        self.assertEqual(result, "Task Title\nTask Description\n")
    
    @patch('subprocess.run')
    def test_inspect_jira_task(self, mock_run):
        """Test inspecting a Jira task via curl"""
        mock_run.return_value.stdout = '{"key": "PROJ-123", "fields": {"summary": "Task Title", "description": "Task Description"}}'
        mock_run.return_value.returncode = 0
        
        with patch.dict(os.environ, {
            'JIRA_BASE_URL': 'https://company.atlassian.net',
            'JIRA_API_TOKEN': 'test-token',
            'JIRA_USER_EMAIL': 'user@company.com'
        }):
            result = inspect_jira_task("PROJ-123")
            
            mock_run.assert_called_once_with([
                "curl", "-s",
                "-H", "Authorization: Bearer test-token",
                "-H", "Content-Type: application/json",
                "https://company.atlassian.net/rest/api/3/issue/PROJ-123"
            ], capture_output=True, text=True, check=True)
            self.assertIn('"summary": "Task Title"', result)
    
    @patch('subprocess.run')
    def test_create_worktree(self, mock_run):
        """Test creating a git worktree"""
        mock_run.return_value.returncode = 0
        
        result = create_worktree("PROJ-123-add-login", "main")
        
        mock_run.assert_called_once_with([
            "git", "worktree", "add", "../PROJ-123-add-login-worktree", "-b", "PROJ-123-add-login", "main"
        ], check=True)
        self.assertTrue(result)
    
    @patch('dev_lifecycle.extensions.task_coding.invoke_writing_plans')
    def test_generate_plan(self, mock_invoke_wp):
        """Test generating implementation plan"""
        mock_invoke_wp.return_value = "plan-123"
        
        plan_id = generate_plan("github", "PROJ-123-add-login")
        
        mock_invoke_wp.assert_called_once_with({
            "phase": "task",
            "provider": "github",
            "steps": ["inspect", "confirm", "worktree", "plan", "implement", "pr", "link", "cleanup"]
        })
        self.assertEqual(plan_id, "plan-123")
    
    @patch('dev_lifecycle.extensions.task_coding.invoke_subagent_development')
    def test_execute_plan(self, mock_invoke_sd):
        """Test executing the plan"""
        mock_invoke_sd.return_value = True
        
        result = execute_plan("plan-123")
        
        mock_invoke_sd.assert_called_once_with("plan-123")
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_create_pr(self, mock_run):
        """Test creating a PR"""
        mock_run.return_value.stdout = "https://github.com/user/repo/pull/456\n"
        mock_run.return_value.returncode = 0
        
        pr_url = create_pr("Add login feature", "This PR adds login functionality", "feature/login")
        
        mock_run.assert_called_once_with([
            "gh", "pr", "create",
            "--title", "Add login feature",
            "--body", "This PR adds login functionality",
            "--base", "feature/login"
        ], capture_output=True, text=True, check=True)
        self.assertEqual(pr_url, "https://github.com/user/repo/pull/456\n")
    
    @patch('subprocess.run')
    def test_link_pr_to_tracker_github(self, mock_run):
        """Test linking PR to GitHub issue"""
        mock_run.return_value.returncode = 0
        
        link_pr_to_tracker("github", 123, 456)
        
        mock_run.assert_called_once_with([
            "gh", "issue", "edit", "123",
            "--add-label", "PR:456"
        ], check=True)
    
    @patch('subprocess.run')
    def test_link_pr_to_tracker_jira(self, mock_run):
        """Test linking PR to Jira issue"""
        mock_run.return_value.returncode = 0
        
        with patch.dict(os.environ, {
            'JIRA_BASE_URL': 'https://company.atlassian.net',
            'JIRA_API_TOKEN': 'test-token',
            'JIRA_USER_EMAIL': 'user@company.com'
        }):
            link_pr_to_tracker("jira", "PROJ-123", "https://github.com/user/repo/pull/456")
            
            # Should post a comment with PR link
            mock_run.assert_called_once()
            args, kwargs = mock_run.call_args
            self.assertIn("curl", args[0])
            self.assertIn("-X", args[0])
            self.assertIn("POST", args[0])
            self.assertIn("/rest/api/3/issue/PROJ-123/comment", " ".join(args[0]))
    
    @patch('subprocess.run')
    def test_cleanup_worktree(self, mock_run):
        """Test cleaning up worktree"""
        mock_run.return_value.returncode = 0
        
        result = cleanup_worktree("../PROJ-123-add-login-worktree")
        
        mock_run.assert_called_once_with([
            "git", "worktree", "remove", "../PROJ-123-add-login-worktree"
        ], check=True)
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()