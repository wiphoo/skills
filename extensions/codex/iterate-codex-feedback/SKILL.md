---
name: iterate-github-feedback-afk
description: Autonomous AFK loop via GitHub CLI (`gh`). Fetches Codex feedback, applies fixes automatically, replies, resolves or leaves unresolved for HITL, and stops on 👍 thumbs-up / clean / blocked / Codex pushback. No user interaction required during loop.
---

# Iterate GitHub Feedback — AFK Mode

**AFK / autonomous:** Runs continuously without user presence. The loop fetches, validates, applies, replies, resolves/unresolves, pushes, and polls every ~180s until a termination condition is met.

## AFK quick start (run once, loop autonomously)

1. Set environment / target PR; run this once — loop continues in background (`nohup`, `screen`, `tmux`).
2. Agent auto-posts `@codex review`, detects 👀 acknowledgement, then enters loop.
3. Each round is fully automatic: fetch → triage → apply / pushback → reply → resolve / leave-unresolved → push.
4. Loop exits automatically on: 👍 thumbs-up, clean review, blocked check failure, or Codex HITL pushback.

## Step-by-step loop

### 1. Initial setup and review acknowledgement

```bash
# Comment to trigger review (top-level PR comments use the issues endpoint)
# Replace {owner} {repo} {number} as needed
gh api -X POST /repos/{owner}/{repo}/issues/{number}/comments \
  -f body='@codex review'

# Look for acknowledgement response (eyes emoji 👀) in the latest comment
# This indicates the reviewer is aware and will provide feedback
```

### 2. Check for immediate termination conditions

```bash
# Count 👍 reactions on the PR itself (PR reactions live on the issues endpoint)
THUMBS_UP=$(gh api /repos/{owner}/{repo}/issues/{number}/reactions 2>/dev/null \
  | jq '[.[] | select(.content == "+1" and (.user.login | startswith("chatgpt-codex-connector")))] | length')

# Check for any ❤️ eyes or review response reactions
REVIEW_RESPONSE=$(gh api /repos/{owner}/{repo}/pulls/{number}/comments 2>/dev/null | jq -r '.[] | select(.body | contains("👀")) | .user.login + " acknowledged"')

if [[ "${THUMBS_UP:-0}" -gt 0 ]]; then
  echo "✓ Reviewer gave 👍 thumbs-up. Stopping loop."
  exit 0
fi

if [[ -n "$REVIEW_RESPONSE" ]]; then
  echo "✓ Reviewer acknowledged with 👀. Starting feedback loop."
fi
```

### 3. Fetch ALL unresolved feedback threads, then delegate to @extensions/github/address-pr-feedback/SKILL.md

```bash
# 1. Fetch ALL unresolved threads (review threads are GraphQL-only; record each thread id, path, line, body, author)
# --paginate follows pageInfo/endCursor so no unresolved thread past the first 100 is missed
UNRESOLVED=$(gh api graphql --paginate -f query='
query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){
  reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
    nodes{id isResolved comments(first:1){nodes{databaseId body path line author{login}}}}}}}}' \
  -f o={owner} -f r={repo} -F n={number} \
  --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not)' | jq -s '.')
THREAD_COUNT=$(echo "$UNRESOLVED" | jq 'length')
echo "Fetched $THREAD_COUNT unresolved feedback threads (full data saved for processing)"

# 2. Process every fetched thread through @extensions/github/address-pr-feedback/SKILL.md:
#    - Read file + surrounding code at thread location
#    - Validate correctness / security / behavior / style / perf / tests / design
#    - Decide APPLY (smallest correct change -> test -> commit -> reply -> resolve)
#    - Or PUSH BACK (reply with reasoning + evidence; do NOT edit/resolve; leave for HITL)
#    - Use CLI reply: gh api -X POST .../pulls/{number}/comments/<comment_id>/replies -f body='...'
#    - Resolve addressed: gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=<thread_id>
#    - Leave pushed-back unresolved (HITL); summarize reasoning
```


### 4. Apply fixes and push updates

For each **valid** feedback:

```bash
# Apply smallest correct change (using address-pr-feedback approach)
# Add/update focused tests
# Run relevant checks
# Commit related changes
# Reply in thread with what changed and test results
# Resolve thread when fully addressed

# Push new commit
# git push origin <branch>   (gh has no push subcommand)
```

### 5. Push-back handling (Human-in-the-loop)

For each **invalid/out-of-scope** feedback:

```bash
# Do NOT edit code or resolve
# Reply with concise reasoning + evidence
# Summarize push-backs for HITL decision
# Leave threads unresolved for human review

echo "=== PUSH BACKS FOR HITL ==="
# Collect all push-back threads with reasoning
```

### 6. Wait for next feedback round

```bash
# Poll for new feedback using GitHub CLI
# Check for new review threads on current head
# Look for:
# - New comments from reviewer
# - Updated review threads
# - Any resolved threads (if we want to track resolution)

# Poll every ~120-270 seconds as mentioned in original
# Exit when:
# - Reviewer adds 👍 thumbs-up
# - Feedback becomes clean (zero actionable comments)
# - All push-backs have been addressed by human
# - Blocked state is detected
```

### 7. Complete loop conditions

The loop stops when ANY of these conditions is met:

#### Condition A: 👍 Thumbs-up reaction
```bash
# Reviewer adds thumbs-up to the PR
# Exit immediately - signals satisfaction
```

#### Condition B: Clean feedback
```bash
# No unresolved threads AND Codex has reviewed the pushed head (zero threads right after a push proves nothing)
HEAD_SHA=$(git rev-parse HEAD)
# --paginate: the reviews endpoint returns 30 per page; emit one line per match and count them across all pages
REVIEWED=$(gh api --paginate /repos/{owner}/{repo}/pulls/{number}/reviews \
  --jq ".[] | select(.user.login | startswith(\"chatgpt-codex-connector\")) | select(.commit_id == \"$HEAD_SHA\") | .id" | wc -l)
# Clean only when THREAD_COUNT == 0 (GraphQL fetch from step 3, re-run after the review) and REVIEWED > 0
```

#### Condition C: Codex pushback needs HITL
```bash
# Only Codex-originated pushbacks trigger this stop condition
# Non-Codex feedback is reported but does not by itself stop the loop
# Report summary and wait for human decision
```

#### Condition D: Blocked state
```bash
# Fix cannot be completed (failing checks, ambiguous request)
# Report block and wait for human intervention
```

## Data extraction commands (GitHub CLI)

```bash
# Get latest commit ID
current_commit=$(gh api /repos/{owner}/{repo}/pulls/{number} | jq -r '.head.sha')

# Fetch review threads (GraphQL only) — see the query in step 3
review_threads="$UNRESOLVED"

# Get comments on PR
comments=$(gh api /repos/{owner}/{repo}/pulls/{number}/comments)

# Get PR reactions
pr_reactions=$(gh api /repos/{owner}/{repo}/issues/{number}/reactions)

# Get user's review on current commit
user_review=$(gh api /repos/{owner}/{repo}/pulls/{number}/reviews | jq -r '.[] | select(.user.login == "target_reviewer")')
```

## Completion summary

Report:
- PR/repo/commit updated
- Number of feedback loops completed
- Per-loop fixed/pushed-back counts
- Final state (👍 / clean / awaiting-human / blocked)
- All push-back threads with reasoning for HITL
- Remaining risks or required reviewer decisions