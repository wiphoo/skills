---
name: address-pr-feedback-codex-github-cli
description: Use GitHub CLI (`gh`) to fetch unresolved PR review feedback, validate each comment, apply fixes or push back with a CLI reply, then either resolve addressed threads or keep pushed-back threads unresolved for human-in-the-loop review. Use when the user asks to address review comments with step-by-step `gh` commands.
---

# Address PR Review Feedback (GitHub CLI)

No MCP required — use `gh` and the REST API directly.

## Quick start (step by step)

1. **Identify the PR**
   - Extract `owner/repo` and PR number from context or ask the user.
   - Confirm auth and repo context: `gh auth status` and `gh repo view`.

2. **Fetch unresolved feedback**
   - Review threads exist only in GraphQL (there is no REST `review_threads` route):
     ```bash
     gh api graphql -f query='
     query($o:String!,$r:String!,$n:Int!,$after:String){repository(owner:$o,name:$r){pullRequest(number:$n){
       reviewThreads(first:100,after:$after){pageInfo{hasNextPage endCursor}
         nodes{id isResolved comments(first:1){nodes{databaseId body path line author{login}}}}}}}}' \
       -f o={owner} -f r={repo} -F n={number} \
       --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)'
     ```
     Repeat with `-f after=<endCursor>` while `hasNextPage` is true.
   - Record for each: thread id (GraphQL node id), path/line, original comment id (`databaseId`), body, author.

3. **Validate every comment**
   - Read the file and surrounding code at the comment location.
   - Classify: correctness / security / behavior / style / performance / tests / design.
   - Decide **apply** or **push back**. Never blindly apply.

4. **Proceed fixed or pushback**
   - **Fix** — apply the smallest correct change, update focused tests, run relevant checks, commit only related files.
   - **Push back** — do **not** edit code or resolve. Reply in the thread with concise reasoning + evidence.

5. **Reply in comment via CLI**
   - Post on the original review comment:  
     `gh api -X POST /repos/{owner}/{repo}/pulls/{number}/comments/<comment_id>/replies -f body='...'`
   - Include what changed and exact check results.

6. **Resolve or keep unresolved**
   - Resolved only when the feedback is fully addressed:  
     `gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=<thread_id>`
   - If a check fails or the fix is incomplete, report it and **leave unresolved**.
   - Pushed-back items stay unresolved for human review.

7. **Human-in-the-loop for pushback**
   - Summarize every pushed-back thread with its reasoning.
   - Wait for the human decision; do not resolve pushed-back threads or force the PR forward.

8. **Linked work items**
   - Resolve the work item only from an explicit URL/identifier, provider link, or branch/title/body reference.
   - Use the tracker's native integration; do not assume Jira keys/statuses for non-Jira trackers.

9. **Commit message**
   - Follow repo conventions from `AGENTS.md` and recent commits.
   - Include the work-item identifier when available:  
     `<work-item-id>: address review feedback — <brief description>`

## Completion summary

Report:
- PR/repo/commit updated
- Threads fetched, applied, pushed back, skipped, unresolved
- Files changed and checks run with exact results
- Threads replied to and resolved
- Pushed-back threads left unresolved for HITL, with reasoning
- Linked work-item source and update result, if any
- Remaining risks or required reviewer decisions
