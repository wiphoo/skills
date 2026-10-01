"""
Extension modules for dev-lifecycle umbrella skill.

Each module implements a specific subcommand's core logic and delegates
to the corresponding existing skill module.
"""

# Import lazily to avoid circular dependencies
__all__ = [
    "task_coding",
    "jira_task_coding", 
    "github_task_coding",
    "pr_feedback",
    "post_merge",
]