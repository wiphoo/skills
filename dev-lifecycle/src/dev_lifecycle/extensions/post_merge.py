"""Post-merge extension for dev-lifecycle umbrella skill."""

import subprocess
import os
import json
import re
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
        # Use gh pr view --json closingIssuesReferences (supported v3 field)
        result = subprocess.run([
            "gh", "pr", "view", str(pr_number),
            "--repo", self.repo,
            "--json", "closingIssuesReferences"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        numbers = sorted({r["number"] for r in data.get("closingIssuesReferences", [])})
        if len(numbers) > 1:
            raise ValueError(f"ambiguous: PR closes multiple issues {numbers}; choose one explicitly")
        return numbers[0] if numbers else None
    
    def detect_issue_jira(self, pr_number: int) -> Optional[str]:
        """Detect the Jira key referenced in the PR branch, title, or body."""
        result = subprocess.run([
            "gh", "pr", "view", str(pr_number),
            "--repo", self.repo,
            "--json", "headRefName,title,body"
        ], capture_output=True, text=True, check=True)

        data = json.loads(result.stdout)
        text = " ".join(data.get(k) or "" for k in ("headRefName", "title", "body"))
        keys = sorted(set(re.findall(r"\b[A-Z][A-Z0-9]+-\d+\b", text)))
        if len(keys) > 1:
            raise ValueError(f"ambiguous: PR references multiple Jira keys {keys}; choose one explicitly")
        return keys[0] if keys else None
    
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
        """Update a Jira issue comment using ADF format."""
        # Jira v3 requires Atlassian Document Format
        adf_body = {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_body}]}]}
        result = subprocess.run([
            "curl", "-s", "--fail-with-body", "-X", "POST",
            f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_key}/comment",
            "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({"body": adf_body})
        ], capture_output=True, text=True, check=True)
        return result.returncode == 0
    
    def transition_status(self, issue_key: str, target_status: str) -> bool:
        """Transition a Jira issue to target status using transition ID."""
        # Fixed: Fetch transitions and match by name, then submit transition ID
        # GET /rest/api/3/issue/{issueKey}/transitions
        result = subprocess.run([
            "curl", "-s", "--fail-with-body", "-X", "GET",
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
                "curl", "-s", "--fail-with-body", "-X", "POST",
                f"{os.environ.get('JIRA_BASE_URL', 'https://atlassian.net')}/rest/api/3/issue/{issue_key}/transitions",
                "-u", f"{os.environ.get('JIRA_USER_EMAIL', 'user')}:{os.environ.get('JIRA_API_TOKEN', 'token')}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({"transition": {"id": transition_id}})
            ], capture_output=True, text=True, check=True)
            return True
        return False
    
    def sync_branch(self, base_branch: str) -> bool:
        """Sync local branch with remote after merge."""
        # Stop on a dirty worktree: `git switch` would carry local edits onto the base branch
        status = subprocess.run(["git", "status", "--porcelain"],
                                capture_output=True, text=True, check=True)
        if status.stdout.strip():
            raise RuntimeError("worktree is dirty; refusing to switch branches")
        subprocess.run(["git", "switch", base_branch], capture_output=True, text=True, check=True)
        subprocess.run(["git", "pull", "--ff-only"], capture_output=True, text=True, check=True)
        return True