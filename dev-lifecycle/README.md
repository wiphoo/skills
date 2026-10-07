# Dev Lifecycle — Umbrella Skill

**Dev Lifecycle** orchestrates the full development lifecycle across three domains:

- **Task Management** — task-coding workflow for GitHub/Jira tasks
- **PR Feedback** — PR review feedback handling (human or codex)
- **Post-Merge** — post-merge updates (Jira/PR status transitions)

---

## Purpose

This umbrella skill provides three deterministic subcommands that guide a code change from issue selection through PR creation, review handling, and post-merge synchronization. It integrates with GitHub (`gh` CLI) and Jira REST API, and delegates to specialized skills for implementation, writing plans, and code‑review handling.

> **Note:** The actual implementation lives under `src/dev_lifecycle/`. This README documents the skill interface and usage.

---

## Subcommands (exact keywords required)

| Subcommand | Required Arguments | Description |
|------------|-------------------|-------------|
| `dev-lifecycle task <provider>` | `provider` (`github` \| `jira`) | Execute the complete task‑coding workflow: inspect → confirm → worktree → plan → implement → PR → link → cleanup |
| `dev-lifecycle pr-feedback <human\|codex>` | `human` or `codex` | Fetch unresolved PR review threads, classify, apply fixes or push back, reply to the correct thread, and resolve |
| `dev-lifecycle post-merge <provider>` | `provider` (`github` \| `jira`) | After a PR is merged, update linked work item and sync local branch |

---

## Tool Contracts

| Provider | Tool | Required Environment Variables |
|----------|------|------------------------------|
| GitHub | `gh` CLI / `gh api` | `GH_TOKEN` or `gh auth login` |
| Jira | `curl` REST | `JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL` |

---

## 1. Task Subcommand: `dev-lifecycle task <provider>`

**Purpose:** Execute the complete task‑coding workflow for GitHub or Jira issues.

**Steps:**

1. **Inspect** — `gh issue view <number>` (GitHub) or `curl …/rest/api/3/issue/<key>` (Jira)
2. **Confirm** — read title, status, assignee, acceptance criteria
3. **Worktree** — `git worktree add ../<name> -b <branch> <base-branch>`; branch naming: `<work-item-id>/<short-description>`
4. **Plan** — invoke `writing-plans` skill with `phase: "task"` and provider‑specific steps
5. **Implement** — execute plan via `subagent-driven-development`
6. **Create PR** — `gh pr create --title "<title>" --body "<body>" --base <base-branch>`
7. **Link to Tracker** — GitHub: `gh issue comment <number> --body "PR opened: <pr-url>"`; Jira: post comment with PR URL
8. **Cleanup** — `git worktree remove ../<name>`

---

## 2. PR‑Feedback Subcommand: `dev-lifecycle pr-feedback <human\|codex>`

**Purpose:** Fetch unresolved PR review threads, classify each, apply fixes or push back, reply to the correct thread, and resolve.

**Steps:**

1. **Fetch Unresolved Threads** — GraphQL only: `gh api graphql` with `pullRequest.reviewThreads { nodes { id isResolved … } }` (see `SKILL.md` for the full query)
2. **Read Context** — read file at comment location using `cat <path> | head -n $((line + 10)) | tail -n 20`
3. **Classify** — `apply` (correctness / security / bug / missing test) vs `pushback` (style preference / out of scope / design disagreement)
4. **Fix & Reply** — apply smallest correct change, then `gh api -X POST "/repos/{owner}/{repo}/pulls/{number}/comments/<comment_id>/replies" -f body="Fixed: …"`
5. **Resolve Thread** — GraphQL `resolveReviewThread(input: {threadId: <thread_id>})` via `gh api graphql` (see `SKILL.md`)

---

## 3. Post‑Merge Subcommand: `dev-lifecycle post-merge <provider>`

**Purpose:** After a PR is merged, update linked work item and sync local branch.

**Steps:**

1. **Confirm Merge** — `gh pr view <number> --json mergedAt,mergeCommit,baseRefName`; continue only if `mergedAt` is non-null and `mergeCommit` present
2. **Detect Issue** — prefer `gh pr view <number> --json closingIssuesReferences`; otherwise list every distinct match in title/body (`… | grep -oE '(([[:alnum:]_.-]+/[[:alnum:]_.-]+)?#[0-9]+|[A-Z]+-[0-9]+)' | sort -u`) and stop unless exactly one remains; keep the repository of an `owner/repo#N` reference as `ISSUE_REPO` (a bare `#N` belongs to the PR's repository)
3. **Update Comments** — GitHub: `gh issue comment <number> --repo "$ISSUE_REPO" --body "PR merged: <url>\nMerge commit: <sha>\nBase branch: <branch>"`; Jira: post comment via REST
4. **Transition Status** — GitHub: add label (`gh issue edit … --repo "$ISSUE_REPO"`); Jira: list the issue's `/transitions`, match by name, and submit that transition ID (not a status ID)
5. **Sync Local Branch** — `git switch <base-branch>` then `git pull --ff-only`

---

## Checklist

```text
[ ] Subcommand matches exactly (task / pr-feedback / post-merge)
[ ] Provider argument provided and valid
[ ] Required tools available (gh / curl + Jira env vars)
[ ] Worktree created and cleaned up (task subcommand)
[ ] Plan generated via writing-plans (task subcommand)
[ ] Plan executed via subagent-driven-development (task subcommand)
[ ] PR created with correct base branch (task subcommand)
[ ] Thread replies post to /comments/<comment_id>/replies (pr-feedback)
[ ] Threads resolved only when fully addressed (pr-feedback)
[ ] Merge confirmed before post-merge actions (post-merge)
[ ] Issue detected from PR metadata (post-merge)
[ ] Comments added to tracker (post-merge)
[ ] Status transitioned correctly (post-merge)
[ ] Local branch synced with --ff-only (post-merge)
```

---

## Dependencies (delegated skills)

| Subcommand | Provider | Delegates To |
|------------|----------|--------------|
| `task` | github | `base/task-coding` + `writing-plans` + `subagent-driven-development` |
| `task` | jira | `extensions/jira/jira-task-coding` + `writing-plans` + `subagent-driven-development` |
| `pr-feedback` | human | `extensions/github/address-pr-feedback` |
| `pr-feedback` | codex | `extensions/codex/iterate-codex-feedback` |
| `post-merge` | github | `base/post-merge-update` |
| `post-merge` | jira | `extensions/post-merge-update` |

---

## Installation

The skill is part of the `wiphoo/skills` repository. Ensure:

1. `GH_TOKEN` is set (or run `gh auth login`)
2. Jira credentials are exported if using Jira providers:
   ```bash
   export JIRA_BASE_URL="https://your-domain.atlassian.net"
   export JIRA_API_TOKEN="your-api-token"
   export JIRA_USER_EMAIL="your@email.com"
   ```

3. Install `gh` CLI and `jq` if not already present.

---

## License

MIT License (see `skills/LICENSE`)