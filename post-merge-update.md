---
name: post-merge-update
description: After a pull request or merge request is merged, update its linked work item in Jira, GitHub Issues, GitLab, Linear, or another tracker, then synchronize the local base branch. Use when the user says a PR/MR was merged or asks to perform post-merge issue updates.
---

# Post-Merge Work-Item Update

## Quick start

Provide the merged PR/MR and desired target status when known:

```text
PR/MR: <provider, repository, and number or URL>
Target status: <source-specific status>
Work item: <optional URL or identifier>
```

## Workflow

### 1. Resolve the merge request

Use the provider's native integration first. For GitHub, use GitHub MCP rather than `gh` or direct API calls. Read the PR/MR number, title, body, source branch, base branch, merge state, merge commit, and linked issues.

If the provider or repository is ambiguous, ask. Do not infer a work item from an unrelated repository or branch.

### 2. Validate the merge

Continue only when the PR/MR is confirmed merged. If it is open, closed without merge, or unavailable, stop and report the exact state. Use the actual base branch from the merge request; never assume `main`.

### 3. Resolve the work item and source

Use, in order:

- An explicitly supplied work-item URL or identifier
- A linked issue shown by the PR/MR provider
- A work-item reference in the source branch, title, body, or commit message

Confirm the identifier and tracker before writing. If no unambiguous item is found, report the merge and ask for the item rather than updating a guessed record.

### 4. Update the source record

Read the work item with its native integration. Add a concise comment containing the PR/MR link, merge commit when available, base branch, and next validation step. If a target status was supplied, fetch available transitions and use the exact source-specific transition matching it. If it is unavailable, report the available choices and do not force a status.

Do not assume Jira, Jira status names, or Jira commands for GitHub Issues, GitLab, Linear, or another tracker. If the source supports comments but not status transitions, add the comment and report that limitation.

### 5. Synchronize the local repository

Before changing branches, check for local modifications and do not discard them. Switch to the merge request's base branch and update it safely:

```bash
git switch <base-branch>
git pull --ff-only
```

If the worktree is dirty, the branch is unavailable, or the pull cannot fast-forward, stop and report the condition without resetting or overwriting local work.

## Completion Report

Report:

- PR/MR and confirmed merge state
- Work-item source and canonical identifier
- Comment and status transition result
- Base branch synchronization result
- Any unresolved ambiguity, unavailable integration, or validation follow-up
