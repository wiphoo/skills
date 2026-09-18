---
name: address-pr-feedback
description: Fetch review feedback from GitHub pull requests, GitLab merge requests, Bitbucket, or another code-hosting source, validate it, apply fixes, run checks, and update linked work items when applicable. Use when the user asks to address review comments, fix PR/MR feedback, or resolve review threads.
---

# Address Review Feedback

## Quick start

1. Identify the PR/MR URL, provider, repository, and number from context or ask the user.
2. Fetch unresolved review threads with the provider's native integration.
3. Validate each comment against the code, tests, and linked requirements.
4. For valid feedback: edit, test, commit, reply, and resolve when supported.
5. Update an unambiguous linked work item when applicable, then summarize the result.

## Workflow

### 1. Identify the review source

Use the provider's native integration first. For GitHub, use GitHub MCP rather than `gh` or direct APIs. For GitLab, Bitbucket, or another provider, use its configured integration. Read the PR/MR metadata, changed files, review threads, current commit, source branch, and base branch.

If the provider, repository, or review request is ambiguous, ask instead of guessing. Focus on unresolved threads; include resolved threads only when the user explicitly requests a full audit.

### 2. Validate each comment

Do not blindly apply suggestions. For every unresolved thread:

1. Read the file and surrounding code at the comment location.
2. Understand whether the request concerns correctness, security, behavior, style, performance, tests, or design.
3. Check whether the proposed change fits actual behavior, project conventions, and existing tests.
4. Cross-reference the linked work item, specification, acceptance criteria, or PR/MR description when available.
5. Decide whether to apply it or push back. If pushing back, reply with concise reasoning and evidence; do not change code or resolve the thread.

### 3. Apply valid feedback

For each logically grouped set of valid comments:

1. Apply the smallest correct change using `apply_patch`.
2. Add or update focused tests when behavior changes.
3. Run relevant checks and record exact results.
4. Review the diff and commit only related files.
5. Reply in the original review thread using the provider's native tool with what changed and test results.
6. Resolve the thread only after the feedback is addressed and the provider supports resolution.

Do not resolve a thread merely because a reply was posted. If a check fails or the fix is incomplete, report it and leave the thread unresolved unless the reviewer explicitly accepts that state.

### 4. Map and update linked work items

Resolve the work item, if any, in this order:

- An explicitly supplied URL or identifier
- A linked issue shown by the PR/MR provider
- A reference in the branch name, title, body, or commit message

Confirm the tracker and identifier before writing. Use its native integration to add a concise per-change comment when supported. Do not assume Jira keys, statuses, commands, or comments for GitHub Issues, GitLab, Linear, or another tracker. If no item is linked or the match is ambiguous, skip the update and report why.

### 5. Commit message

Follow repository conventions from `AGENTS.md` and recent commits. Include the work-item identifier when available; otherwise describe the review fix directly:

```text
<work-item-id>: address review feedback — <brief description>
```

## Completion Summary

Report:

- Review source, PR/MR, and commit updated
- Number of threads applied, pushed back, skipped, or unresolved
- Files changed and checks run with honest results
- Threads replied to and resolved
- Linked work-item source and update result, if any
- Remaining risks, failed checks, or required reviewer decisions
