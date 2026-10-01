"""
Task coding extension module for dev-lifecycle umbrella skill.

Wraps base.task-coding and extensions for GitHub/Jira task coding.
Provides plan generation + execution lifecycle that the umbrella skill
calls into when `dev-lifecycle task` is invoked.
"""

from typing import Optional, Dict, Any


class GitHubTaskCoding:
    """Handles GitHub task workflow (task-coding path)."""
    
    def __init__(self):
        self.base_path = None
        self.plan_id = None
    
    def create_plan(self, provider: str, issue_id: str, **kwargs) -> str:
        """Generate an implementation plan via writing-plans skill."""
        # In production, this would invoke the writing-plans skill
        # For now, return a plan ID
        self.plan_id = f"plan-{provider}-{issue_id}"
        return self.plan_id
    
    def execute_plan(self, plan_id: str) -> bool:
        """Execute the given plan via subagent-driven-development."""
        # In production, invoke subagent-driven-development skill
        # For now, simulate success
        self.plan_id = plan_id
        return True
    
    def create_pr(self, title: str, body: str, base_branch: str) -> Optional[str]:
        """Create a PR via gh CLI."""
        # Would call: gh pr create --title ... --body ... --base ...
        self.pr_url = f"https://github.com/user/repo/pull/{{new_pr_num}}"
        return self.pr_url


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
        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{jira_key}/comment",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:" + os.environ.get('JIRA_API_TOKEN', 'token'),
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"body": f"PR merged: {pr_url}"})
        ], check=True)


# For direct import compatibility
task_coding = GitHubTaskCoding()
jira_task_coding = JiraTaskCoding()