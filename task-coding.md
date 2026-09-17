---
name: task-coding
description: Pick up work items from Jira, GitHub Issues, GitLab, Linear, or another issue tracker, implement the change, add tests, create a pull request, and keep the source record truthful. Use when the user asks to start, implement, or complete an issue, ticket, task, or coding assignment.
---

# Issue Task Coding
## Purpose

Take a tracked work item from ready-to-code through implementation and pull request. Keep the work item, branch, commits, tests, and PR aligned with reality. Preserve this skill name for existing callers; the input is not limited to Jira.

## Source Handling
1. Identify the source from the provided URL, key, number, repository context, or explicit user instruction.
2. Resolve the canonical work-item URL and identifier. If more than one item matches, ask instead of guessing.
3. Read the item with its native integration first: Jira MCP for Jira, GitHub MCP for GitHub, or the configured integration for another provider.
4. Read title, description, acceptance criteria, comments, links, attachments, labels, priority, assignee, status, and related PRs when available.
5. If the source cannot be read or updated, report that limitation and continue only when the user explicitly accepts a no-sync workflow.

## Rules
- Do not assume requirements that are not written or confirmed.
- If requirements are ambiguous, use the `grill-me` skill before planning or coding.
- Explore the repository to answer questions that code can answer; ask the user for product decisions.
- Do not claim a status, implementation, test, deployment, or review that has not happened.
- Use the source's actual status names and available transitions. Never invent a Jira workflow for another tracker.
- Use provider-native MCP tools for issue and pull-request operations. Follow the GitHub MCP rule for GitHub.
- Never hide failed, skipped, or unavailable checks.

## Workflow
### 1. Inspect and confirm readiness
Read the work item and repository before editing. It should define a problem, expected behavior, acceptance criteria, scope, and enough test intent to act. If not actionable, document the gap and stop or mark the source blocked using its own workflow.

### 2. Clarify and plan
After requirements are confirmed, create a short plan covering affected modules, assumptions, risks, and test strategy. Post the plan to the source when supported, then move it to the source's equivalent of actively working. If no equivalent exists, leave status unchanged and record the plan in the PR or a comment.

### 3. Create a branch
Use `<work-item-id>/<short-description>` when an identifier exists, otherwise `<short-description>`. Use lowercase hyphens and the repository's actual default branch as the base. Do not reuse an unrelated branch.

### 4. Implement and test
Inspect existing architecture and patterns before changing code. Keep the change focused, preserve auth, validation, logging, and compatibility, and do not add secrets. Add deterministic tests for success, failure, permissions, and relevant edge cases using the project's existing style.

### 5. Run checks
Run the repository's relevant test, lint, typecheck, build, and security checks. Record exact commands and honest results. If a check cannot run, state why and assess the risk.

### 6. Commit and create the PR
Review the diff and commit only related files. Include the work-item identifier in the commit and PR title when available. Use the provider's native PR/MR integration and include:

```markdown
## Summary
- ...

## Work item
- <canonical URL or "not linked">

## Tests
- `<command>`: passed/failed/not run (reason)

## Risk and limitations
- ...
```

Create the PR only after implementation and relevant checks are complete. Move the work item to its source-specific equivalent of review only after the PR exists, and add the PR link and result summary.

### 7. Handle blockers and completion
If blocked, stop coding and record the blocker, completed work, remaining work, required input, branch, and commit in the source or PR. After merge or deployment, move through the source's actual validation and completion states only when their conditions are met. Never mark complete before acceptance criteria are validated.

## Semantic Status Guide
Use this only to understand reality, not to rename statuses:

| Reality | Meaning |
|---|---|
| Ready | Can be picked up |
| Active | Being implemented |
| Blocked | Needs external input |
| Review | PR/MR exists and awaits review |
| Validation | Ready for QA or acceptance testing |
| Complete | Acceptance criteria validated |
| Cancelled | No longer needed |

## Checklist
```text
[ ] Identify and read the source work item
[ ] Confirm requirements and acceptance criteria
[ ] Clarify unresolved decisions with grill-me
[ ] Post plan and mark active when supported
[ ] Create a focused branch
[ ] Inspect, implement, and test
[ ] Run and record relevant checks
[ ] Review diff and create PR
[ ] Link PR and update source truthfully
[ ] Validate before marking complete
```
