# Implementation Plan: Dev Lifecycle Umbrella Skill

## Overview
Build the `dev-lifecycle` skill that orchestrates three subcommands:
- `dev-lifecycle task <provider>` – task-coding workflow
- `dev-lifecycle pr-feedback <human|codex>` – PR review feedback handling
- `dev-lifecycle post-merge <provider>` – post-merge update workflow

## Phase 1: Skill Skeleton & Core Structure

### 1.1 Directory & File Layout
```
dev-lifecycle/
├── IMPLEMENTATION-PLAN.md          ← this file
├── README.md                       ← skill overview
├── src/
│   ├── __init__.py
│   ├── dev_lifecycle.py            ← main skill module
│   │   ├── __init__
│   │   └── _routing.py             ← subcommand dispatcher
│   └── extensions/
│       ├── task_coding.py          ← task-coding wrapper
│       ├── jira_task_coding.py     ← Jira task variant
│       ├── github_task_coding.py   ← GitHub task variant
│       ├── pr_feedback.py          ← PR feedback handler
│       ├── post_merge.py           ← post-merge updater
│       └── post_merge_jira.py      ← Jira post-merge variant
└── tests/
    ├── test_dev_lifecycle.py
    └── conftest.py
```

### 1.2 Main Module (`src/dev_lifecycle/dev_lifecycle.py`)
- Import `subagent-driven-development` for task execution
- Import `writing-plans` for phase planning
- Define `_routing()` function that parses subcommand + provider args
- Register subcommands as functions
- Export `dev_lifecycle` package

### 1.3 Subcommand Implementations

#### `task <provider>`
- Call `writing-plans` with parameters:
  - `phase`: "task"
  - `provider`: "github" or "jira"
  - `steps`: [inspect, confirm, worktree, plan, implement, pr, link, cleanup]
- Delegate to `task_coding` extension module
- Return plan ID for traceability

#### `pr-feedback <human|codex>`
- Fetch PR via `gh api`
- List unresolved review threads
- For each thread:
  - Read file + surrounding code
  - Classify: apply / pushback
  - If apply: edit file, run tests, commit
  - Reply to SAME thread via `gh api -X POST .../comments -f in_reply_to=<thread_comment_id>`
  - Mark thread as resolved
- Return thread IDs processed

#### `post-merge <provider>`
- Confirm merge via `gh pr view --json merged`
- Detect issues via `gh pr view --jq 'title+.body'` or grep `[A-Z]+-[0-9]+`
- For each issue:
  - Update comment via `curl -X POST .../issue/<key>/comments` (Jira) or `gh issue comment <n>` (GitHub)
  - Transition status via `curl .../transitions` (Jira) or `gh issue edit --add-label` (GitHub)
  - Sync local branch: `git switch <base>; git pull --ff-only`

## Phase 2: Extension Modules

### 2.1 Task Coding Wrapper
- `src/dev_lifecycle/extensions/task_coding.py`
- Wraps `base/task-coding` module
- Provides `create_plan()`, `execute_plan()`, `get_plan()`
- Handles Jira-specific branching (e.g., Jira issue key → branch name)

### 2.2 PR Feedback Handler
- `src/dev_lifecycle/extensions/pr_feedback.py`
- Implements `fetch_unresolved()`, `classify_and_fix()`, `reply_to_thread()`
- Uses `gh` CLI for fetching and replying
- Tracks thread state per PR

### 2.3 Post-Merge Updater
- `src/dev_lifecycle/extensions/post_merge.py`
- Handles both Jira (REST API) and GitHub (gh CLI) post-merge updates
- Confirms merge before acting
- Applies status transitions and comment updates

## Phase 3: Integration & Testing

### 3.1 Unit Tests
- Test routing logic for each subcommand
- Mock `gh` and `curl` calls in tests
- Verify thread reply format (correct `in_reply_to`)
- Verify post-merge status transitions

### 3.2 Integration Tests
- End-to-end: task → PR → post-merge flow
- Verify worktree creation/cleanup
- Verify PR comment replies target correct thread

## Success Criteria
- `dev-lifecycle task github` → creates plan, runs subagent, creates PR
- `dev-lifecycle pr-feedback PR-123` → fetches threads, replies to each, marks resolved
- `dev-lifecycle post-merge PR-456` → confirms merge, updates comments, syncs branch
- All three subcommands are reachable via exact keyword invocation
- No hidden routing logic; every path is explicit in code

## Dependencies
- `writing-plans` skill (must be installed/available)
- `subagent-driven-development` skill (for task execution)
- `gh` CLI (GitHub) and/or `curl` + Jira API (Jira)
- Existing `base/task-coding`, `extensions/jira/jira-task-coding`, `extensions/github/address-pr-feedback`, `extensions/codex/iterate-codex-feedback` modules

## Risks & Mitigations
- **Tool availability**: Ensure `gh` is installed and authenticated; Jira env vars (`JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL`) are set.
- **Thread targeting**: Must ensure `in_reply_to` points to the correct comment ID within each thread.
- **Branch naming**: Task subcommand should derive branch name from provider + optional issue key (e.g., `my-project/task-abc`).
- **Error handling**: Each subcommand should catch failures and return meaningful errors without crashing.

## Timeline
- Day 1: Scaffold directory, core module, subcommand skeleton
- Day 2: Implement task subcommand + writing-plans integration
- Day 3: Implement PR-feedback subcommand + gh CLI integration
- Day 4: Implement post-merge subcommand + Jira REST integration
- Day 5: Write tests, integrate, and review
