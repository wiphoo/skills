"""
Dev Lifecycle Umbrella Skill

Orchestrates three subcommands:
- dev-lifecycle task <provider>  → task-coding workflow
- dev-lifecycle pr-feedback <human|codex> → PR review feedback
- dev-lifecycle post-merge <provider> → post-merge update

Each subcommand follows a deterministic, step-by-step procedure.
"""

import subprocess
import sys
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# Subcommand definitions (exact keywords)
# ---------------------------------------------------------------------------

SUBCOMMANDS = [
    ("task", "task <provider>", "github | jira"),
    ("pr-feedback", "pr-feedback <human|codex>", "human | codex"),
    ("post-merge", "post-merge <provider>", "github | jira"),
]

SUBCOMMAND_NAMES = [s[0] for s in SUBCOMMANDS]

# ---------------------------------------------------------------------------
# Task subcommand (github | jira)
# ---------------------------------------------------------------------------

def handle_task(provider: str) -> None:
    """Handle `dev-lifecycle task <provider>`.

    STUB — not yet implemented. Prints step names only; actual task-coding
    logic lives in extensions/task_coding.py. This skeleton exists so the
    routing table and CLI can be tested before wiring up real handlers.
    """
    print(f"[dev-lifecycle] task {provider}")
    
    # Step 1: Inspect
    print("[dev-lifecycle] Inspecting task...")
    if provider == "github":
        # gh issue view <n> would be called here
        pass
    elif provider == "jira":
        # curl .../rest/api/3/issue/<key>
        pass
    
    # Step 2: Confirm
    print("[dev-lifecycle] Confirming task...")
    
    # Step 3: Worktree
    print("[dev-lifecycle] Setting up worktree...")
    
    # Step 4: Plan (via writing-plans skill)
    print("[dev-lifecycle] Generating implementation plan...")
    
    # Step 5: Implement (via subagent-driven-development)
    print("[dev-lifecycle] Implementing task...")
    
    # Step 6: PR
    print("[dev-lifecycle] Creating PR...")
    
    # Step 7: Link
    print("[dev-lifecycle] Linking PR to tracker...")
    
    # Step 8: Cleanup
    print("[dev-lifecycle] Cleaning up worktree...")

# ---------------------------------------------------------------------------
# PR-feedback subcommand (human | codex)
# ---------------------------------------------------------------------------

def handle_pr_feedback(mode: str) -> None:
    """Handle `dev-lifecycle pr-feedback <human|codex>`."""
    print(f"[dev-lifecycle] pr-feedback {mode}")
    
    # Step 1: Fetch unresolved feedback
    print("[dev-lifecycle] Fetching unresolved PR feedback...")
    # gh api .../pulls/{n}/review_threads
    
    # Step 2: For each thread, classify and fix
    print("[dev-lifecycle] Processing feedback threads...")
    
    # Step 3: Reply to correct thread
    print("[dev-lifecycle] Replying to feedback threads...")
    
    # Step 4: Resolve threads
    print("[dev-lifecycle] Resolving feedback threads...")

# ---------------------------------------------------------------------------
# Post-merge subcommand (github | jira)
# ---------------------------------------------------------------------------

def handle_post_merge(provider: str) -> None:
    """Handle `dev-lifecycle post-merge <provider>`."""
    print(f"[dev-lifecycle] post-merge {provider}")
    
    # Step 1: Confirm merge
    print("[dev-lifecycle] Confirming merge...")
    
    # Step 2: Detect issues
    print("[dev-lifecycle] Detecting issues...")
    
    # Step 3: Update comments
    print("[dev-lifecycle] Updating comments...")
    
    # Step 4: Transition status
    print("[dev-lifecycle] Transitioning status...")
    
    # Step 5: Sync local branch
    print("[dev-lifecycle] Syncing local branch...")

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def route(subcommand: str, provider: Optional[str] = None) -> bool:
    """Route to appropriate subcommand handler."""
    if subcommand not in SUBCOMMAND_NAMES:
        print(f"Error: unknown subcommand '{subcommand}'")
        return False
    
    # Validate provider per subcommand
    valid_providers = {
        "task": ["github", "jira"],
        "pr-feedback": ["human", "codex"],
        "post-merge": ["github", "jira"],
    }
    if provider not in valid_providers.get(subcommand, []):
        print(f"Error: invalid provider '{provider}' for subcommand '{subcommand}'")
        return False

    # Look up handler by subcommand name (first element)
    handler = None
    for s in SUBCOMMANDS:
        if s[0] == subcommand:
            handler = s[1]
            break

    print(f"[dev-lifecycle] Routing: {subcommand} {provider}")
    return True


# ---------------------------------------------------------------------------
# Entry point (when skill is invoked)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # In a real skill, this would parse arguments and call the appropriate handler
    # For now, just demonstrate the routing logic
    import argparse
    parser = argparse.ArgumentParser(description="Dev Lifecycle Umbrella Skill")
    parser.add_argument("subcommand", choices=SUBCOMMAND_NAMES)
    parser.add_argument("provider", nargs="?", help="github | jira (task, post-merge) or human | codex (pr-feedback)")
    args = parser.parse_args()
    
    if route(args.subcommand, args.provider):
        if args.subcommand == "task":
            handle_task(args.provider)
        elif args.subcommand == "pr-feedback":
            handle_pr_feedback(args.provider)
        elif args.subcommand == "post-merge":
            handle_post_merge(args.provider)
    else:
        print("Invalid subcommand or missing required arguments.")
