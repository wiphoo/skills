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
gh pr view <number> --json state,mergedAt,mergeCommit,baseRefName,title,body,url,headRefName
```

If using a non-GitHub provider, use its CLI or REST API. Stop if not merged.

### 2. Validate the merge

Continue only when `mergedAt` is non-null and a `mergeCommit` is present. Use the actual base branch (`baseRefName`) from the PR/MR; never assume `main`.

```bash
MERGED_AT=$(gh pr view <number> --json mergedAt --jq '.mergedAt // empty')
if [[ -z "$MERGED_AT" ]]; then
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

- Jira: matches `[A-Z][A-Z0-9]+-[0-9]+`
- GitHub Issues: matches `#123` or issue URL

If ambiguous, ask rather than guess. Prefer GitHub's closing references; otherwise collect every distinct match and stop unless exactly one remains (a PR saying `Related #10 … Fixes #20` must not silently pick `#10`):

```bash
# 1. An explicitly supplied work item (quick start `Work item:`) always wins over inference.
#    WORK_ITEM may be PROJ-123, #42, owner/repo#42, a GitHub issue URL, or a Jira /browse/ URL.
if [[ -n "${WORK_ITEM:-}" ]]; then
  case "$WORK_ITEM" in
    https://github.com/*/issues/*) ISSUE_REF=$(echo "$WORK_ITEM" | sed -E 's|https://github\.com/([^/]+/[^/]+)/issues/([0-9]+).*|\1#\2|') ;;
    */browse/*)                    ISSUE_REF=$(echo "$WORK_ITEM" | sed -E 's|.*/browse/([A-Z][A-Z0-9]+-[0-9]+).*|\1|') ;;
    *)                             ISSUE_REF="$WORK_ITEM" ;;
  esac
else
  # 2. Otherwise infer it from the PR: closing references first, then every distinct match
  CLOSING=$(gh pr view <number> --json closingIssuesReferences --jq '.closingIssuesReferences[] | "\(.repository.owner.login)/\(.repository.name)#\(.number)"')
  CANDIDATES=${CLOSING:-$(gh pr view <number> --json title,body --jq '.title + " " + .body' \
    | grep -oE '([A-Z][A-Z0-9]+-[0-9]+|([[:alnum:]_.-]+/[[:alnum:]_.-]+)?#[0-9]+)' | sort -u)}
  if [[ $(echo "$CANDIDATES" | grep -c .) -ne 1 ]]; then
    echo "❌ Ambiguous or missing work item (candidates: ${CANDIDATES:-none}). Ask the user."; exit 1
  fi
  ISSUE_REF="$CANDIDATES"
fi
# A reference like owner/repo#42 keeps its own repository; a bare #42 belongs to the PR's repository
if [[ "$ISSUE_REF" == */*#* ]]; then ISSUE_REPO="${ISSUE_REF%%#*}"; else ISSUE_REPO="<PR owner/repo>"; fi
```

### 4. Update the source record

#### 4.1 Jira update (curl)

Add comment (Jira v3 requires an ADF body and the singular `/comment` resource):

```bash
jq -n --arg t "PR merged: <URL> | Merge commit: <COMMIT> | Base branch: <BASE_BRANCH>" \
  '{body:{type:"doc",version:1,content:[{type:"paragraph",content:[{type:"text",text:$t}]}]}}' \
| curl -s --fail-with-body -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/comment" \
  -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
  -H "Content-Type: application/json" -d @-
```

Transition status only if a target was supplied (`TARGET_STATUS` non-empty) — a comment-only update must not call the transitions endpoint:

```bash
if [[ -n "$TARGET_STATUS" ]]; then
  # The transitions endpoint takes a transition ID, not a status ID
  TRANSITIONS=$(curl -s --fail-with-body "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
    -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json")
  TRANSITION_ID=$(echo "$TRANSITIONS" | jq -r ".transitions[] | select(.name == \"$TARGET_STATUS\") | .id")
  if [[ -n "$TRANSITION_ID" ]]; then
    # Bash does not stop on curl's error 22 (--fail-with-body); test its status before reporting success
    if curl -s --fail-with-body -X POST "$JIRA_BASE_URL/rest/api/3/issue/$JIRA_ISSUE/transitions" \
      -u "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"transition\": {\"id\": \"$TRANSITION_ID\"}}"; then
      echo "✅ Issue $JIRA_ISSUE transitioned to $TARGET_STATUS"
    else
      echo "❌ Jira rejected the transition to $TARGET_STATUS"; exit 1
    fi
  else
    echo "⚠️ Target status \"$TARGET_STATUS\" not found."
  fi
fi
```

#### 4.2 GitHub Issues update (gh)

The issue may live in a different repository than the current checkout. Choose `ISSUE_REPO` once and pass it on every issue command: the repository from an explicit issue URL or `owner/repo#N` when one was supplied (never replace it with the PR's repository), otherwise the PR's repository resolved in step 1:

```bash
# ISSUE_REPO was set in step 3: the repo of an owner/repo#N reference or explicit issue URL, else the PR's repo
gh issue comment <issue_number> --repo "$ISSUE_REPO" --body "PR merged: <URL>\nMerge commit: <COMMIT>\nBase branch: <BASE_BRANCH>"
```

Update status via label or field (if using GitHub Projects):

```bash
if [[ -n "$TARGET_STATUS" ]]; then
  gh issue edit <issue_number> --repo "$ISSUE_REPO" --add-label "$TARGET_STATUS"
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
