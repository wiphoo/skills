# gh-discussion-manager — Reference

Linked workflow: `extensions/github/address-pr-feedback/SKILL.md`

## Step-by-step commands

### 1. Identify PR
- `gh auth status`
- `gh repo view --json nameWithOwner`
- `gh pr view {pr} --json url,reviews,comments`

### 2. Fetch unresolved feedback
- GraphQL (review threads have no REST route): `gh api graphql --paginate` over `pullRequest.reviewThreads { pageInfo { hasNextPage endCursor } nodes { id isResolved root: comments(first:1) { nodes { databaseId path body } } latest: comments(last:1) { nodes { databaseId createdAt body } } } }`
  Filter: `.isResolved | not` (see `scripts/gh-discuss.sh` for a working query)

Record: thread id, diff hunk, path/line, original comment id, body, author.

### 3. Validate
Read file at comment location; classify (correctness / security / behavior / style / performance / tests / design). Decide **apply** or **push back**.

### 4. Reply via CLI
- Inline/reply: `gh api -X POST repos/{o}/{r}/pulls/{pr}/comments/<comment_id>/replies -f body="Reply + evidence"`
- Top-level PR: `gh pr comment {pr} --body "..."`

### 5. Resolve / keep unresolved
- Resolved when fully addressed: `gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=<thread_id>`
- If incomplete/check fails, report and **leave unresolved**.
- Pushed-back threads stay unresolved for HITL.

### 6. Emoji/status
- `gh api repos/{o}/{r}/issues/{pr}/reactions --jq '.[] | {content:.content, user:.user.login}'`
- `gh pr view {pr} --json reviews,reactionGroups`
