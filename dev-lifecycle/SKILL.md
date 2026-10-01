---
name: dev-lifecycle
description: Use when managing the full development lifecycle as an agent — starting a task from a GitHub issue or Jira ticket, handling PR review feedback in a conversation, or updating a work item after a merge.
---

# Dev Lifecycle — Umbrella Skill

Orchestrates the full development lifecycle across three domains:
- **Task Management** — task-coding workflow for GitHub/Jira tasks
- **PR Feedback** — PR review feedback handling (human or codex)
- **Post-Merge** — post-merge updates (Jira/PR status transitions)

## Tool Contracts

| Provider | Tool | Required Env Vars |
|----------|------|-------------------|
| GitHub | `gh` CLI / `gh api` | `GH_TOKEN` or `gh auth login` |
| Jira | `curl` REST | `JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL` |

## Subcommands (exact keywords required)

| Subcommand | Required Arguments | Description |
|------------|---------------------|-------------|
| `dev-lifecycle task <provider>` | `provider` (github \| jira) | Task coding workflow |
| `dev-lifecycle pr-feedback <human\|codex>` | `human` or `codex` | PR review feedback |
| `dev-lifecycle post-merge <provider>` | `provider` (github \| jira) | Post-merge update |

**Routing rules:**
- Subcommand must match exactly (`task`, `pr-feedback`, `post-merge`)
- Missing provider raises an error
- Unknown subcommand raises an error

---

## 1. Task Subcommand: `dev-lifecycle task <provider>`

### Purpose
Execute the complete task-coding workflow for GitHub or Jira issues.

### Steps

#### Step 1: Inspect
```bash
# GitHub
gh issue view <issue-number>

# Jira
curl -s -H "Authorization: Bearer $JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  "$JIRA_BASE_URL/rest/api/3/issue/<issue-key>"
```

#### Step 2: Confirm
Read title, status, assignee, acceptance criteria. If not actionable, document gap and stop.

#### Step 3: Worktree
```bash
git worktree add ../<worktree-name> -b <branch-name> <base-branch>
```
Branch naming: `<work-item-id>/<short-description>` (lowercase hyphens)

#### Step 4: Plan
Invoke `writing-plans` skill to create implementation plan:
```bash
# Plan parameters
phase: "task"
provider: "<github|jira>"
steps: ["inspect", "confirm", "worktree", "plan", "implement", "pr", "link", "cleanup"]
```

#### Step 5: Implement
Execute plan via `subagent-driven-development` skill.

#### Step 6: Create PR
```bash
gh pr create --title "<title>" --body "<body>" --base <base-branch>
```

#### Step 7: Link to Tracker
```bash
# GitHub
gh issue edit <issue-number> --add-label "PR:<pr-number>"

# Jira
curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/<issue-key>/comment" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "PR merged: <pr-url>"}'
```

#### Step 8: Cleanup
```bash
git worktree remove ../<worktree-name>
```

---

## 2. PR-Feedback Subcommand: `dev-lifecycle pr-feedback <human|codex>`

### Purpose
Fetch unresolved PR review threads, classify each, apply fixes or push back, reply to correct thread, and resolve.

### Steps

#### Step 1: Fetch Unresolved Threads
```bash
gh api "/repos/{owner}/{repo}/pulls/{number}/review_threads?per_page=100" \
  | jq '.[] | select(.state != "RESOLVED")'
```
Record for each: `thread_id`, `path`, `line`, `comment_id`, `body`, `author`.

#### Step 2: For Each Thread — Read Context
```bash
# Read file at comment location
cat <path> | head -n $((line + 10)) | tail -n 20
```

#### Step 3: Classify
Classify feedback as **apply** or **pushback**:
- **apply** — correctness / security / behavior / bug / typo / missing test
- **pushback** — style preference / out of scope / design disagreement (with evidence)

#### Step 4: Fix & Reply to SAME Thread
```bash
# Apply smallest correct change, add/update tests, run checks, commit

# Reply to thread (CRITICAL: use in_reply_to=<comment_id>)
gh api -X POST "/repos/{owner}/{repo}/pulls/{number}/comments" \
  -f body="Fixed: <what changed>; tests pass (<results>)" \
  -f in_reply_to=<comment_id>
```
**Key requirement:** Reply must target the exact comment ID from the thread.

#### Step 5: Resolve Thread
```bash
gh api -X PATCH "/repos/{owner}/{repo}/pulls/{number}/review_threads/{thread_id}" \
  -f resolved=true
```
Leave unresolved if check fails or pushback.

---

## 3. Post-Merge Subcommand: `dev-lifecycle post-merge <provider>`

### Purpose
After a PR is merged, update linked work item and sync local branch.

### Steps

#### Step 1: Confirm Merge
```bash
gh pr view <number> --json merged,mergeCommit,baseRef
```
Continue only if `merged: true` and `mergeCommit` present. Use actual `baseRef`.

#### Step 2: Detect Issue
```bash
# GitHub: extract from PR title/body
gh pr view <number> --jq '.title + .body' | grep -oE '(#[0-9]+|[A-Z]+-[0-9]+)' | head -1

# Jira: same pattern match from title/body/branch
```

#### Step 3: Update Comments
```bash
# GitHub
gh issue comment <issue-number> --body "PR merged: <url>\nMerge commit: <sha>\nBase branch: <branch>"

# Jira
curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/<issue-key>/comments" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body": "PR merged: <url>\nMerge commit: <sha>\nBase branch: <branch>"}'
```

#### Step 4: Transition Status
```bash
# GitHub (via label)
gh issue edit <issue-number> --add-label "<target-status>"

# Jira (via transition ID)
PROJECT_KEY=$(echo "$ISSUE_KEY" | cut -d- -f1)
STATUS_ID=$(curl -s "$JIRA_BASE_URL/rest/api/3/project/$PROJECT_KEY/statuses" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" \
  | jq -r ".[] | select(.name == \"<target-status>\") | .id")
if [ -n "$STATUS_ID" ]; then
  curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/$ISSUE_KEY/transitions" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"transition\": {\"id\": \"$STATUS_ID\"}}"
fi
```

#### Step 5: Sync Local Branch
```bash
git switch <base-branch>
git pull --ff-only
```
Stop if worktree dirty, branch unavailable, or pull cannot fast-forward.

---

## Delegation Map

| Subcommand | Provider | Delegates To |
|------------|----------|--------------|
| `task` | github | `base/task-coding` + `writing-plans` + `subagent-driven-development` |
| `task` | jira | `extensions/jira/jira-task-coding` + `writing-plans` + `subagent-driven-development` |
| `pr-feedback` | human | `extensions/github/address-pr-feedback` |
| `pr-feedback` | codex | `extensions/codex/iterate-codex-feedback` |
| `post-merge` | github | `base/post-merge-update` |
| `post-merge` | jira | `extensions/post-merge-update` |

*Exact delegation mapping will be refined in implementation plan*

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
[ ] Thread replies use in_reply_to=<comment_id> (pr-feedback)
[ ] Threads resolved only when fully addressed (pr-feedback)
[ ] Merge confirmed before post-merge actions (post-merge)
[ ] Issue detected from PR metadata (post-merge)
[ ] Comments added to tracker (post-merge)
[ ] Status transitioned correctly (post-merge)
[ ] Local branch synced with --ff-only (post-merge)
```

## License
MIT License (see `skills/LICENSE`)