---
name: gh-discussion-manager
description: Manage GitHub PR and discussion threads via gh CLI — fetch unresolved discussions, reply to threads, resolve or keep unresolved, and check emoji/review status. Use when working with PR reviews/discussion threads or when user asks to reply, resolve, or inspect PR discussion state via gh. See REFERENCE.md for full step-by-step workflow linked from @extensions/github/address-pr-feedback/SKILL.md.
---

# gh-discussion-manager

Quick reference for `gh` CLI PR/discussion commands. Detailed steps in [REFERENCE.md](REFERENCE.md).

## Quick start

```bash
# Confirm repo / PR
gh repo view --json nameWithOwner
gh pr view {pr} --json url,reviews

# Fetch unresolved review threads
# (review threads are GraphQL-only; --paginate follows pageInfo)
gh api graphql --paginate -f query='
query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
  reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
    nodes{id isResolved comments(first:1){nodes{databaseId path body}}}}}}}' \
  -f o={o} -f r={r} -F n={pr} \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)'

# Reply to thread (comment_id = first comment's databaseId)
gh api -X POST repos/{o}/{r}/pulls/{pr}/comments/{comment_id}/replies -f body="..."

# Resolve thread (thread id = GraphQL node id)
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id={id}

# Emoji/status
gh api repos/{o}/{r}/issues/{pr}/reactions --jq '.[] | {content:.content, user:.user.login}'
```

## Workflows (summary)

- **Fetch unresolved**: GraphQL `reviewThreads` filtered on `isResolved == false`.
- **Reply**: `POST .../comments/{comment_id}/replies`; `gh pr comment` for top-level.
- **Resolve**: GraphQL `resolveReviewThread`. Leave unresolved for HITL when pushed back.
- **Check status**: reactions via `issues/{pr}/reactions`; reviews via `gh pr view`.

## Scripts

`scripts/gh-discuss.sh` — unresolved thread query template.
