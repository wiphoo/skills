---
name: update-work-item
description: Update a Jira story/task/sub-task or a GitHub issue by adding a comment and changing its status/state using GitHub CLI (`gh`) or Jira REST API via `curl`. Supports both trackers in one workflow.
---
# Update Work Item (Jira / GitHub)

Add comments and change status/state for Jira (story / task / sub-task) or GitHub Issues using `gh` or `curl`. No MCP required.

## Quick start

Provide the work item and intended update:

```text
Tracker: jira | github
Work item: PROJ-123 (Jira) or #42 / owner/repo#42 (GitHub)
Comment: <optional message>
New status/state: <optional — Jira transition name or GitHub label/state>
```

## Prerequisites

For Jira:

```bash
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_API_TOKEN="your-personal-api-token"
export JIRA_USER_EMAIL="your-email@example.com"
```

Ensure `gh` is authenticated for GitHub.

---

## Workflow

### 1. Identify tracker and issue key/number

Determine source from identifier or ask:

- Jira: `PROJ-123`, `PROJ-456` — any issue type (story, task, sub-task, bug)
- GitHub: `#42`, `owner/repo#42`, or issue URL

If ambiguous, ask rather than guess.

```bash
# Basic extraction from input
ISSUE_REF="$1"
if echo "$ISSUE_REF" | grep -qE '^[A-Z]+-[0-9]+$'; then
  TRACKER="jira"
  JIRA_ISSUE="$ISSUE_REF"
elif echo "$ISSUE_REF" | grep -qE '#[0-9]+'; then
  TRACKER="github"
  GITHUB_ISSUE=$(echo "$ISSUE_REF" | grep -oE '#[0-9]+' | tr -d '#')
else
  echo "❌ Cannot determine tracker from: $ISSUE_REF"
  exit 1
fi
```

### 2. Add comment

#### Jira (curl)

```bash
curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/comments" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"body\": \"$COMMENT_BODY\"}"
```

Works for any issue type — story, task, sub-task, bug, epic.

#### GitHub (gh)

```bash
gh issue comment "$GITHUB_ISSUE" --body "$COMMENT_BODY"
```

### 3. Change status / state

#### Jira — transition status (story / task / sub-task / any)

Fetch available transitions for the issue:

```bash
TRANSITIONS=$(curl -s "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Accept: application/json")

echo "$TRANSITIONS" | jq -r '.transitions[] | .name'
```

Apply transition by name or ID:

```bash
# Find transition ID by name
TRANSITION_ID=$(echo "$TRANSITIONS" | jq -r ".transitions[] | select(.name == \"$TARGET_STATUS\") | .id")

if [[ -n "$TRANSITION_ID" ]]; then
  curl -s -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"transition\": {\"id\": \"$TRANSITION_ID\"}}"
  echo "✅ $JIRA_ISSUE transitioned to $TARGET_STATUS"
else
  echo "⚠️ Transition '$TARGET_STATUS' not found. Available:"
  echo "$TRANSITIONS" | jq -r '.transitions[] | .name'
fi
```

> Works for story, task, sub-task, bug, epic — any Jira issue type that supports transitions.

#### GitHub — change state / label

Update label or close/reopen (state change):

```bash
# Add label (acts as state marker if using labels for status)
if [[ -n "$TARGET_STATUS" ]]; then
  gh issue edit "$GITHUB_ISSUE" --add-label "$TARGET_STATUS"
fi

# Close / reopen (direct state change)
if [[ "$TARGET_STATUS" == "done" || "$TARGET_STATUS" == "closed" ]]; then
  gh issue close "$GITHUB_ISSUE"
elif [[ "$TARGET_STATUS" == "reopen" ]]; then
  gh issue reopen "$GITHUB_ISSUE"
fi
```

If the project uses GitHub Project fields (status field), you may need to update via `gh api` instead of label change.

---

## Data extraction commands (GitHub CLI / curl)

```bash
# Jira — get issue details (includes type: story/task/sub-task/etc.)
curl -s "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" | jq '{key, fields: {issuetype: .fields.issuetype.name, status: .fields.status.name, summary: .fields.summary}}'

# GitHub — get issue state
gh issue view "$GITHUB_ISSUE" --json number,title,state,labels,body
```

---

## Completion report

Report:
- Tracker detected (jira / github)
- Issue key / number updated
- Comment added (yes / excerpt)
- Status / state changed (new value or unchanged)
- Issue type noted (Jira: story/task/sub-task/etc.)
- Any missing transition/label or error
description: Update a Jira story/task/sub-task or a GitHub issue by adding a comment and changing its status/state. Uses `gh` for GitHub and `curl` for Jira REST API. Supports any Jira issue type (story, task, sub-task, bug, epic).