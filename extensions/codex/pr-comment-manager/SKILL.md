---
name: pr-comment-manager
description: Fetch unresolved PR review threads via `gh`, proceed with fix or pushback, reply via CLI, and either resolve or leave unresolved for HITL review.
---

# Address PR Feedback — GitHub CLI Step-by-Step

No MCP — pure `gh` / GraphQL.

## 1. Fetch unresolved feedback

Review threads exist only in GraphQL (there is no REST `review_threads` route). `--paginate` follows `pageInfo` for you:

```bash
gh api graphql --paginate -f query='
query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
  reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
    nodes{id isResolved root:comments(first:1){nodes{databaseId body path line author{login}}} latest:comments(last:1){nodes{databaseId createdAt body author{login}}}}}}}}' \
  -f o={owner} -f r={repo} -F n={number} \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)'
```
Record for each: `thread_id` (node `id`), `path`, `line`, `body`, `comment_id` (`databaseId`), `author`.

## 2. Proceed fixed or pushback

- **Fixed** — apply smallest correct change (`edit` / `apply_patch`), add/update focused tests, run relevant checks, commit only related files.
- **Pushback** — reply with concise reasoning + evidence; do NOT edit code or resolve.

Always read file and surrounding code at the comment location before deciding. Never blindly apply.

## 3. Reply in comment via CLI

```bash
gh api -X POST /repos/{owner}/{repo}/pulls/{number}/comments/<comment_id>/replies \
  -f body='Fixed: changed X; tests pass (results: ...)'
```

For pushback:
```bash
gh api -X POST /repos/{owner}/{repo}/pulls/{number}/comments/<comment_id>/replies \
  -f body='Pushback: reason; evidence: ...'
```

Always include what changed and exact check results.

## 4. Resolve or keep unresolved for HITL

- **Fixed and verified** → resolve:
  ```bash
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' \
    -f id=<thread_id>
  ```
- **Failed / incomplete** → leave unresolved; report honestly. Do NOT resolve on a failing fix.
- **Pushback** → leave unresolved; summarize reasoning for HITL review. Wait for human decision; do not resolve pushed-back threads or force PR forward.

---

See `@extensions/github/address-pr-feedback/SKILL.md` for the full workflow including commit conventions and linked work-item updates.
