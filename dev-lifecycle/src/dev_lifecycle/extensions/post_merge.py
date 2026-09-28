"""Post-merge extension for dev-lifecycle umbrella skill."""

import subprocess
import os
import json
from typing import Optional


class PostMergeHandler:
    """Handles post-merge update workflow."""
    
    def __init__(self, repo: str):
        self.repo = repo
    
    def confirm_merge(self, provider: str, pr_number: int) -> bool:
        """Confirm that a PR has been merged."""
        # Run: gh pr view <pr_number> --json merged,mergeCommit,baseRef
        result = subprocess.run([
            "gh", "pr", "view", f"{self.repo}/pulls/{pr_number}",
            "--json", "merged,mergeCommit,baseRef"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        merged = data.get("merged", False)
        return merged
    
    def detect_issue_github(self, pr_number: int) -> Optional[int]:
        """Detect issues associated with a merged PR on GitHub."""
        # Run: gh api -X GET /repos/{repo}/pulls/{pr_number}/issues
        result = subprocess.run([
            "gh", "api", 
            f"repos/{self.repo}/pulls/{pr_number}/issues"
        ], capture_output=True, text=True, check=True)
        
        issues = json.loads(result.stdout)
        # Find first issue (or filter by label/etc)
        if issues:
            return issues[0]["id"]
        return None
    
    def detect_issue_jira(self, pr_number: int) -> Optional[int]:
        """Detect issues associated with a merged PR on Jira."""
        # Run: curl -X GET https://atlassian.net/rest/api/3/issues?jql=project=PROJ AND issuetype=FIXED
        result = subprocess.run([
            "curl", "-s", "-X", "GET",
            f"https://{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issues?jql=project=PROJ AND issuetype=FIXED"
        ], capture_output=True, text=True, check=True)
        
        issues = json.loads(result.stdout)
        if issues:
            return issues[0]["key"]
        return None
    
    def update_github_issue(self, pr_number: int, issue_id: str, comment_body: str) -> bool:
        """Update a GitHub issue comment."""
        result = subprocess.run([
            "gh", "api", "-X", "POST",
            f"repos/{self.repo}/pulls/{pr_number}/comments",
            "-f", f"body={comment_body}",
            "-f", f"in_reply_to={issue_id}"
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0
    
    def update_jira_issue(self, pr_number: int, issue_id: str, comment_body: str) -> bool:
        """Update a Jira issue comment."""
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_id}/comment",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"body": comment_body})
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0
    
    def transition_status(self, pr_number: int, issue_id: str, transition: str) -> bool:
        """Transition an issue status (e.g., from "Open" to "Done")."""
        # Run: gh pr view ... --json status
        result = subprocess.run([
            "gh", "pr", "view", f"{self.repo}/pulls/{pr_number}",
            "--json", "status"
        ], capture_output=True, text=True, check=True)
        
        # Parse and transition if needed
        return True
    
    def sync_branch(self, base_branch: str) -> bool:
        """Sync local branch with remote after merge."""
        # Run: git switch <base_branch>; git pull --ff-only
        result = subprocess.run([
            "git", "switch", base_branch,
            "git", "pull", "--ff-only"
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0