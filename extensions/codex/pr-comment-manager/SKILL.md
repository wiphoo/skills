---
name: pr-comment-manager
description: Fetch unresolved PR review threads via `gh`, proceed with fix or pushback, reply via CLI, and either resolve or leave unresolved for HITL review.
---

# Address PR Feedback — GitHub CLI Step-by-Step

No MCP — pure `gh` / REST.

## 1. Fetch unresolved feedback

```bash
gh api /repos/{owner}/{repo}/pulls/{number}/review_threads?per_page=100 | jq '.[] | select(.state != "RESOLVED")'
```
Record for each: `thread_id`, `path`, `line`, `body`, `comment_id`, `author`.

## 2. Proceed fixed or pushback

- **Fixed** — apply smallest correct change (`edit` / `apply_patch`), add/update focused tests, run relevant checks, commit only related files.
- **Pushback** — reply with concise reasoning + evidence; do NOT edit code or resolve.

Always read file and surrounding code at the comment location before deciding. Never blindly apply.

## 3. Reply in comment via CLI

```bash
gh api -X POST /repos/{owner}/{repo}/pulls/{number}/comments \
  -f body='Fixed: changed X; tests pass (results: ...)' \
  -f in_reply_to=<comment_id>
```

For pushback:
```bash
gh api -X POST /repos/{owner}/{repo}/pulls/{number}/comments \
  -f body='Pushback: reason; evidence: ...' \
  -f in_reply_to=<comment_id>
```

Always include what changed and exact check results.

## 4. Resolve or keep unresolved for HITL

- **Fixed and verified** → resolve:
  ```bash
  gh api -X PATCH /repos/{owner}/{repo}/pulls/{number}/review_threads/{thread_id} \
    -f resolved=true
  ```
- **Failed / incomplete** → leave unresolved; report honestly. Do NOT resolve on a failing fix.
- **Pushback** → leave unresolved; summarize reasoning for HITL review. Wait for human decision; do not resolve pushed-back threads or force PR forward.

---

See `@extensions/github/addree-github-pr-feedback.md` for the full workflow including commit conventions and linked work-item updates.
