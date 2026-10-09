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
if echo "$ISSUE_REF" | grep -qE '^[A-Z][A-Z0-9]+-[0-9]+$'; then
  TRACKER="jira"
  JIRA_ISSUE="$ISSUE_REF"
elif echo "$ISSUE_REF" | grep -qE 'github\.com/[^/]+/[^/]+/issues/[0-9]+'; then
  # Issue URL: take both the repo and the number from it
  TRACKER="github"
  GITHUB_REPO=$(echo "$ISSUE_REF" | sed -E 's#.*github\.com/([^/]+/[^/]+)/issues/.*#\1#')
  GITHUB_ISSUE=$(echo "$ISSUE_REF" | sed -E 's#.*/issues/([0-9]+).*#\1#')
  GH_REPO=(--repo "$GITHUB_REPO")
elif echo "$ISSUE_REF" | grep -qE '#[0-9]+'; then
  TRACKER="github"
  GITHUB_ISSUE=$(echo "$ISSUE_REF" | grep -oE '#[0-9]+' | tr -d '#')
  # Keep the repo from `owner/repo#42`; bare `#42` uses the current repo
  GITHUB_REPO=$(echo "$ISSUE_REF" | grep -oE '^[^/#]+/[^#]+' || true)
  GH_REPO=(); [[ -n "$GITHUB_REPO" ]] && GH_REPO=(--repo "$GITHUB_REPO")
else
  echo "❌ Cannot determine tracker from: $ISSUE_REF"
  exit 1
fi
```

### 2. Add comment

#### Jira (curl)

Skip this step when no comment was requested (`COMMENT_BODY` empty) — both trackers reject an empty body:

```bash
if [[ -n "$COMMENT_BODY" ]]; then
  COMMENT_JSON=$(jq -n --arg t "$COMMENT_BODY" \
    '{body:{type:"doc",version:1,content:[{type:"paragraph",content:[{type:"text",text:$t}]}]}}' \
  )
  curl -s --fail-with-body -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/comment" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    -H "Content-Type: application/json" -d "$COMMENT_JSON" \
    || { echo "❌ Could not add Jira comment to $JIRA_ISSUE"; exit 1; }
fi
```

Works for any issue type — story, task, sub-task, bug, epic.

#### GitHub (gh)

```bash
[[ -n "$COMMENT_BODY" ]] && gh issue comment "$GITHUB_ISSUE" "${GH_REPO[@]}" --body "$COMMENT_BODY"
```

### 3. Change status / state

#### Jira — transition status (story / task / sub-task / any)

Only when a status was requested (`TARGET_STATUS` non-empty) — a comment-only update must not call the transitions endpoint:

```bash
if [[ -n "$TARGET_STATUS" ]]; then
  # Fetch available transitions for the issue
  TRANSITIONS=$(curl -s --fail-with-body "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
    -H "Accept: application/json") \
    || { echo "❌ Could not list Jira transitions for $JIRA_ISSUE"; exit 1; }  # a failed lookup must not look like 'status not found'

  # Find transition ID by name
  TRANSITION_ID=$(echo "$TRANSITIONS" | jq -r ".transitions[] | select(.name == \"$TARGET_STATUS\") | .id")

  if [[ -n "$TRANSITION_ID" ]]; then
    # --fail-with-body makes curl exit non-zero on 4xx/5xx; only report success when it does not
    if curl -s --fail-with-body -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
      -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"transition\": {\"id\": \"$TRANSITION_ID\"}}"; then
      echo "✅ $JIRA_ISSUE transitioned to $TARGET_STATUS"
    else
      echo "❌ Jira rejected the transition to $TARGET_STATUS"; exit 1
    fi
  else
    echo "⚠️ Transition '$TARGET_STATUS' not found. Available:"
    echo "$TRANSITIONS" | jq -r '.transitions[] | .name'
  fi
fi
```

> Works for story, task, sub-task, bug, epic — any Jira issue type that supports transitions.

#### GitHub — change state / label

Update label or close/reopen (state change):

```bash
# Reserved state values change the issue state directly; anything else is treated
# as an existing label name (`--add-label` fails if the label does not exist)
case "$TARGET_STATUS" in
  "")             ;;  # no status change requested
  done|closed)    gh issue close  "$GITHUB_ISSUE" "${GH_REPO[@]}" ;;
  reopen)         gh issue reopen "$GITHUB_ISSUE" "${GH_REPO[@]}" ;;
  *)              gh issue edit   "$GITHUB_ISSUE" "${GH_REPO[@]}" --add-label "$TARGET_STATUS" ;;
esac
```

If the project uses GitHub Project fields (status field), you may need to update via `gh api` instead of label change.

---

## Data extraction commands (GitHub CLI / curl)

```bash
# Jira — get issue details (includes type: story/task/sub-task/etc.)
curl -s "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" | jq '{key, fields: {issuetype: .fields.issuetype.name, status: .fields.status.name, summary: .fields.summary}}'

# GitHub — get issue state
gh issue view "$GITHUB_ISSUE" "${GH_REPO[@]}" --json number,title,state,labels,body
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
