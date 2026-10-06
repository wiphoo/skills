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
gh api repos/{o}/{r}/pulls/{pr}/review_threads --jq '.[] | select(.state!="RESOLVED") | {id:.id, path:.path, body:.comments[0].body}'

# Reply to thread
gh api -X POST repos/{o}/{r}/pulls/{pr}/comments -f body="..." -f in_reply_to={id}

# Resolve thread
gh api -X PATCH repos/{o}/{r}/pulls/{pr}/review_threads/{id} -f resolved=true

# Emoji/status
gh api repos/{o}/{r}/issues/{pr}/reactions --jq '.[] | {content:.content, user:.user.login}'
```

## Workflows (summary)

- **Fetch unresolved**: `review_threads` + `comments` with `unresolved==true`.
- **Reply**: `POST .../comments` with `in_reply_to`; `gh pr comment` for top-level.
- **Resolve**: `PATCH .../review_threads/{id}`. Leave unresolved for HITL when pushed back.
- **Check status**: reactions via `issues/{pr}/reactions`; reviews via `gh pr view`.

## Scripts

`scripts/gh-discuss.sh` — unresolved thread query template.
