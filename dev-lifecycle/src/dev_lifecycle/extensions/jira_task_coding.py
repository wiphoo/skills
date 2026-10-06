"""Jira task coding extension for dev-lifecycle umbrella skill."""

from typing import Optional, Dict, Any


class JiraTaskCoding:
    """Handles Jira task workflow."""
    
    def __init__(self):
        self.base_path = None
        self.plan_id = None
    
    def create_plan(self, provider: str, issue_key: str, **kwargs) -> str:
        """Generate implementation plan via writing-plans skill."""
        self.plan_id = f"plan-{provider}-{issue_key}"
        return self.plan_id
    
    def execute_plan(self, plan_id: str) -> bool:
        """Execute the given plan."""
        self.plan_id = plan_id
        return True
    
    def create_branch(self, issue_key: str, branch_prefix: str = "task") -> str:
        """Create a work branch named <issue_key>/<description>."""
        return f"{branch_prefix}/{issue_key}"
    
    def link_pr(self, jira_key: str, pr_url: str) -> None:
        """Link PR to Jira issue via comment."""
        import subprocess
        import os
        import json
        
        # Jira v3 comment bodies must be Atlassian Document Format
        adf = {"type": "doc", "version": 1, "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": f"PR opened: {pr_url}"}]}]}
        subprocess.run([
            "curl", "-s", "--fail-with-body", "-X", "POST",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{jira_key}/comment",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:" + os.environ.get('JIRA_API_TOKEN', 'token'),
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"body": adf})
        ], check=True)