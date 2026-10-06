"""PR feedback extension for dev-lifecycle umbrella skill."""

import json
import subprocess
from typing import Any, Dict, List

# Review-thread listing and resolution exist only in the GraphQL API.
THREADS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $number) {
      reviewThreads(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          comments(first: 50) {
            nodes { databaseId body path line author { login } }
          }
        }
      }
    }
  }
}
"""

RESOLVE_MUTATION = """
mutation($id: ID!) {
  resolveReviewThread(input: {threadId: $id}) { thread { isResolved } }
}
"""


class PRFeedbackHandler:
    """Handles PR review feedback workflow."""

    def __init__(self, repo: str):
        self.repo = repo

    def fetch_unresolved_threads(self, pr_number: int) -> List[Dict[str, Any]]:
        """Fetch unresolved review threads (GraphQL node id + first comment)."""
        owner, name = self.repo.split("/", 1)
        unresolved: List[Dict[str, Any]] = []
        cursor = None
        while True:
            cmd = [
                "gh", "api", "graphql",
                "-f", f"query={THREADS_QUERY}",
                "-f", f"owner={owner}",
                "-f", f"name={name}",
                "-F", f"number={pr_number}",
            ]
            if cursor:
                cmd += ["-f", f"after={cursor}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            page = json.loads(result.stdout)["data"]["repository"]["pullRequest"]["reviewThreads"]
            unresolved += [t for t in page["nodes"] if not t["isResolved"]]
            if not page["pageInfo"]["hasNextPage"]:
                return unresolved
            cursor = page["pageInfo"]["endCursor"]

    def classify_feedback(self, file_path: str, line: int, feedback_body: str) -> str:
        """Classify feedback as 'apply' or 'pushback'."""
        # In production, would read file + surrounding code
        # For now, simple heuristic: if contains "fix", "bug", "error" -> apply
        feedback_lower = feedback_body.lower()
        if any(word in feedback_lower for word in ["fix", "bug", "error", "typo", "missing"]):
            return "apply"
        return "pushback"

    def reply_to_thread(self, pr_number: int, comment_id: int,
                        feedback_body: str, classification: str, fix_details: str = "") -> bool:
        """Reply in the thread that owns `comment_id`."""
        if classification == "apply":
            body = f"Fixed: {fix_details}"
        else:
            body = f"Pushback: {feedback_body}"

        result = subprocess.run([
            "gh", "api", "-X", "POST",
            f"repos/{self.repo}/pulls/{pr_number}/comments/{comment_id}/replies",
            "-f", f"body={body}",
        ], capture_output=True, text=True, check=True)

        return result.returncode == 0

    def resolve_thread(self, thread_id: str) -> bool:
        """Resolve a review thread by its GraphQL node id."""
        result = subprocess.run([
            "gh", "api", "graphql",
            "-f", f"query={RESOLVE_MUTATION}",
            "-f", f"id={thread_id}",
        ], capture_output=True, text=True, check=True)

        return result.returncode == 0
