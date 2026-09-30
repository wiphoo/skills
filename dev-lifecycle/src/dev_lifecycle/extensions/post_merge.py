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
        # Fixed: Use PR number as positional argument with --repo, not repo/pulls selector
        # gh pr view <number> --repo <owner/repo> --json mergedAt,baseRefName
        result = subprocess.run([
            "gh", "pr", "view", str(pr_number),
            "--repo", self.repo,
            "--json", "mergedAt,baseRefName"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        # mergedAt is present when merged; baseRefName is the target branch
        merged = data.get("mergedAt") is not None
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
    
    def update_github_issue(self, issue_number: int, comment_body: str) -> bool:
        """Update a GitHub issue with a comment."""
        # Fixed: Use issue number (not PR number) for issue comments
        result = subprocess.run([
            "gh", "api", "-X", "POST",
            f"repos/{self.repo}/issues/{issue_number}/comments",
            "-f", f"body={comment_body}"
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0
    
    def update_jira_issue(self, issue_key: str, comment_body: str) -> bool:
        """Update a Jira issue comment."""
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_key}/comment",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"body": comment_body})
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0
    
    def transition_status(self, issue_key: str, target_status: str) -> bool:
        """Transition a Jira issue to target status using transition ID."""
        # Fixed: Fetch transitions and match by name, then submit transition ID
        # GET /rest/api/3/issue/{issueKey}/transitions
        result = subprocess.run([
            "curl", "-s", "-X", "GET",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_key}/transitions",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
            "-H", "Accept: application/json"
        ], capture_output=True, text=True, check=True)
        
        transitions = json.loads(result.stdout).get("transitions", [])
        transition_id = None
        for t in transitions:
            if t["name"].lower() == target_status.lower():
                transition_id = t["id"]
                break
        
        if transition_id:
            subprocess.run([
                "curl", "-s", "-X", "POST",
                f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_key}/transitions",
                "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"transition": {"id": transition_id}})
            ], capture_output=True, text=True, check=True)
            return True
        return False
    
    def sync_branch(self, base_branch: str) -> bool:
        """Sync local branch with remote after merge."""
        # Fixed: Run git switch and git pull as separate subprocesses
        subprocess.run(["git", "switch", base_branch], capture_output=True, text=True, check=True)
        subprocess.run(["git", "pull", "--ff-only"], capture_output=True, text=True, check=True)
        return True