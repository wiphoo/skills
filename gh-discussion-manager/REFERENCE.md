# gh-discussion-manager — Reference

Linked workflow: `extensions/github/addree-github-pr-feedback.md`

## Step-by-step commands

### 1. Identify PR
- `gh auth status`
- `gh repo view --json nameWithOwner`
- `gh pr view {pr} --json url,reviews,comments`

### 2. Fetch unresolved feedback
- `gh api repos/{o}/{r}/pulls/{pr}/review_threads?per_page=100`
  Filter: `.state != "RESOLVED"`
- `gh api repos/{o}/{r}/pulls/{pr}/comments`
  Filter: `.unresolved == true`

Record: thread id, diff hunk, path/line, original comment id, body, author.

### 3. Validate
Read file at comment location; classify (correctness / security / behavior / style / performance / tests / design). Decide **apply** or **push back**.

### 4. Reply via CLI
- Inline/reply: `gh api -X POST repos/{o}/{r}/pulls/{pr}/comments -f body="Reply + evidence" -f in_reply_to=<comment_id>`
- Top-level PR: `gh pr comment {pr} --body "..."`

### 5. Resolve / keep unresolved
- Resolved when fully addressed: `gh api -X PATCH repos/{o}/{r}/pulls/{pr}/review_threads/{thread_id} -f resolved=true`
- If incomplete/check fails, report and **leave unresolved**.
- Pushed-back threads stay unresolved for HITL.

### 6. Emoji/status
- `gh api repos/{o}/{r}/issues/{pr}/reactions --jq '.[] | {content:.content, user:.user.login}'`
- `gh pr view {pr} --json reviews,reactions`
