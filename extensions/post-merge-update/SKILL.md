---
name: post-merge-update-generic
description: After a pull request or merge request is merged, update its linked Jira or GitHub issue, then synchronize the local base branch. Uses `gh` for GitHub PR/MR and `curl` for Jira REST API. No MCP required.
---
# Post-Merge Work-Item Update (generic)

Supports **Jira** and **GitHub Issues**. Use `gh` for GitHub PR/MR metadata and `curl` for Jira updates.

## Quick start

Provide the merged PR/MR and desired target status when known:

```text
PR/MR: <provider, repository, and number or URL>
Target status: <optional Jira status name or GitHub label/field>
Work item: <optional Jira key PROJ-123, GitHub issue #123, or URL>
```

## Prerequisites

For Jira updates:

```bash
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_API_TOKEN="your-personal-api-token"
export JIRA_USER_EMAIL="your-email@example.com"
```

Ensure `gh` is authenticated for GitHub operations.

## Workflow

### 1. Resolve the merge request

Use `gh` to read merged PR/MR metadata. Extract merge commit, base branch, title, body, and any linked issue references.

```bash
gh pr view <number> --json status,merged,mergeCommit,baseRef,title,body,url,headRefName
```

If using a non-GitHub provider, use its CLI or REST API. Stop if not merged.

### 2. Validate the merge

Continue only when `merged` is true and a `mergeCommit` is present. Use the actual base branch from the PR/MR; never assume `main`.

```bash
MERGED=$(gh pr view <number> --jq '.merged')
if [[ "$MERGED" != "true" ]]; then
  echo "❌ PR is not merged. Abort."
  exit 1
fi
```

### 3. Resolve the work item and source

Determine the tracker and identifier in order:

1. Explicitly supplied URL/identifier
2. Linked issue in PR title/body (`PROJ-123` for Jira, `#123` for GitHub)
3. Reference in branch name, title, body, or commit message

Detect source:

- Jira: matches `[A-Z]+-[0-9]+`
- GitHub Issues: matches `#123` or issue URL

If ambiguous, ask rather than guess.

```bash
ISSUE_REF=$(gh pr view <number> --jq '.title + .body' | grep -oE '([A-Z]+-[0-9]+|#[0-9]+)' | head -n1)
```

### 4. Update the source record

#### 4.1 Jira update (curl)

Add comment:

```bash
curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/comments" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"body\": \"PR merged: <URL>\nMerge commit: <COMMIT>\nBase branch: <BASE_BRANCH>\"}"
```

Transition status if target supplied:

```bash
PROJECT_KEY=$(echo "$JIRA_ISSUE" | cut -d- -f1)
STATUS_RESPONSE=$(curl -s "$JIRA_BASE_URL/rest/api/3/project/$PROJECT_KEY/statuses" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json")
TARGET_STATUS_ID=$(echo "$STATUS_RESPONSE" | jq -r ".[] | select(.name == \"$TARGET_STATUS\") | .id")
if [[ -n "$TARGET_STATUS_ID" ]]; then
  curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"transition\": {\"id\": \"$TARGET_STATUS_ID\"}}"
  echo "✅ Issue $JIRA_ISSUE transitioned to $TARGET_STATUS"
else
  echo "⚠️ Target status \"$TARGET_STATUS\" not found."
fi
```

#### 4.2 GitHub Issues update (gh)

Add comment:

```bash
gh issue comment <issue_number> --body "PR merged: <URL>\nMerge commit: <COMMIT>\nBase branch: <BASE_BRANCH>"
```

Update status via label or field (if using GitHub Projects):

```bash
if [[ -n "$TARGET_STATUS" ]]; then
  gh issue edit <issue_number> --add-label "$TARGET_STATUS"
fi
```

If the source supports comments but not status transitions, add the comment and report the limitation.

### 5. Synchronize the local repository

```bash
git switch <base-branch>
git pull --ff-only
```

If the worktree is dirty, the branch is unavailable, or the pull cannot fast-forward, stop and report the condition without resetting or overwriting local work.

## Completion Report

Report:
- PR/MR and confirmed merge state
- Tracker source and canonical identifier
- Jira comment/transition result or GitHub comment/label result
- Base branch synchronization result
- Any unresolved ambiguity or follow-up required
