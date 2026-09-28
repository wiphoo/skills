"""PR feedback extension for dev-lifecycle umbrella skill."""

import os
import subprocess
import json
from typing import List, Dict, Any, Optional


class PRFeedbackHandler:
    """Handles PR review feedback workflow."""
    
    def __init__(self, repo: str):
        self.repo = repo
    
    def fetch_unresolved_threads(self, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch all unresolved review threads for a PR."""
        # Run: gh api /repos/{repo}/pulls/{pr_number}/review_threads?per_page=100
        result = subprocess.run([
            "gh", "api", 
            f"repos/{self.repo}/pulls/{pr_number}/review_threads?per_page=100"
        ], capture_output=True, text=True, check=True)
        
        data = json.loads(result.stdout)
        # Filter unresolved threads
        unresolved = [
            thread for thread in data 
            if thread.get("state") != "RESOLVED"
        ]
        return unresolved
    
    def classify_feedback(self, file_path: str, line: int, feedback_body: str) -> str:
        """Classify feedback as 'apply' or 'pushback'."""
        # In production, would read file + surrounding code
        # For now, simple heuristic: if contains "fix", "bug", "error" -> apply
        feedback_lower = feedback_body.lower()
        if any(word in feedback_lower for word in ["fix", "bug", "error", "typo", "missing"]):
            return "apply"
        return "pushback"
    
    def reply_to_thread(self, pr_number: int, thread_id: int, comment_id: int, 
                       feedback_body: str, classification: str, fix_details: str = "") -> bool:
        """Reply to a specific thread with fix or pushback."""
        body = ""
        if classification == "apply":
            body = f"Fixed: {fix_details}"
        else:
            body = f"Pushback: {feedback_body}"
        
        # Run: gh api -X POST /repos/{repo}/pulls/{pr_number}/comments -f body='...' -f in_reply_to=<comment_id>
        result = subprocess.run([
            "gh", "api", "-X", "POST",
            f"repos/{self.repo}/pulls/{pr_number}/comments",
            "-f", f"body={body}",
            "-f", f"in_reply_to={comment_id}"
        ], capture_output=True, text=True, check=True)
        
        return result.returncode == 0
    
    def resolve_thread(self, pr_number: int, thread_id: int) -> bool:
        """Mark a feedback thread as resolved."""
        # Run: gh api -X PATCH /repos/{repo}/pulls/{pr_number}/review_threads/{thread_id} -f resolved=true
        result = subprocess.run([
            "gh", "api", "-X", "PATCH",
            f"repos/{self.repo}/pulls/{pr_number}/review_threads/{thread_id}",
            "-f", "resolved=true"
        ], capture_output=True, text=True, check=True)
        
        return result.returncode == 0