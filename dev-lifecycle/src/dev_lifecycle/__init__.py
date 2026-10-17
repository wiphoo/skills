"""
Dev Lifecycle Umbrella Skill package.

Orchestrates three subcommands:
- dev-lifecycle task <provider>  → task-coding workflow
- dev-lifecycle pr-feedback <human|codex> → PR review feedback
- dev-lifecycle post-merge <provider> → post-merge update

Each subcommand follows a deterministic, step-by-step procedure.
"""

from . import core  # noqa: F401
from . import extensions  # noqa: F401

__version__ = "1.0.0"