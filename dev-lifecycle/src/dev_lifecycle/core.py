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

    Not implemented: raises instead of printing fake progress. The workflow lives in
    SKILL.md and extensions/task_coding.py; wire this handler to those classes to enable it.
    """
    raise NotImplementedError(f"dev-lifecycle task {provider}: CLI handler not implemented; follow SKILL.md")

# ---------------------------------------------------------------------------
# PR-feedback subcommand (human | codex)
# ---------------------------------------------------------------------------

def handle_pr_feedback(mode: str) -> None:
    """Handle `dev-lifecycle pr-feedback <human|codex>` (not implemented, see handle_task)."""
    raise NotImplementedError(f"dev-lifecycle pr-feedback {mode}: CLI handler not implemented; follow SKILL.md")

# ---------------------------------------------------------------------------
# Post-merge subcommand (github | jira)
# ---------------------------------------------------------------------------

def handle_post_merge(provider: str) -> None:
    """Handle `dev-lifecycle post-merge <provider>` (not implemented, see handle_task)."""
    raise NotImplementedError(f"dev-lifecycle post-merge {provider}: CLI handler not implemented; follow SKILL.md")

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

HANDLERS = {"task": handle_task, "pr-feedback": handle_pr_feedback, "post-merge": handle_post_merge}


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Dev Lifecycle Umbrella Skill")
    parser.add_argument("subcommand", choices=SUBCOMMAND_NAMES)
    parser.add_argument("provider", nargs="?", help="github | jira (task, post-merge) or human | codex (pr-feedback)")
    args = parser.parse_args(argv)

    if not route(args.subcommand, args.provider):
        return 2
    try:
        HANDLERS[args.subcommand](args.provider)
    except NotImplementedError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
