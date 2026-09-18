---
name: iterate-codex-feedback
description: Iterate a PR through rounds of Codex review — fetch each round of Codex feedback, fix or push back on every item, push fixes and loop until Codex has no further feedback, and stop for a human decision on any pushed-back item. Use when the user asks to iterate/loop on Codex PR review, drive a PR to Codex approval, or keep addressing Codex comments until clean.
---

# Iterate Codex Feedback

Drive one PR through repeated Codex review rounds until Codex is satisfied or a
human must decide. Each item is either **fixed** (loop) or **pushed back** (wait).

## Quick start

1. Identify the PR (URL/repo/number) and confirm Codex is the reviewer.
2. Run one round with [address-pr-feedback](../address-pr-feedback/SKILL.md).
3. Fix path → push, wait for Codex to re-review, repeat.
4. Push-back path → reply, then stop and wait for the human.
5. No new Codex feedback → done.

## The loop

Repeat this round until a stop condition (below) is hit:

### 1. Fetch this round's Codex feedback

Fetch unresolved review threads authored by Codex (bot login `chatgpt-codex-connector`
or the repo's configured Codex reviewer) on the current head commit, via GitHub MCP.
Ignore human/other-bot threads unless the user says otherwise.

### 2. Triage every item — fix or push back

Use `address-pr-feedback`'s validation (read the code, judge correctness/security/
behavior/convention). For each thread choose exactly one:

- **Fix** — the feedback is valid.
- **Push back** — the feedback is wrong, out of scope, or a false positive. Reply
  in the thread with concise reasoning + evidence. Do NOT edit code or resolve it.

### 3. Apply fixes and push

If any item was a Fix: apply the smallest correct changes, add/adjust tests, run
checks, commit, reply in each fixed thread with what changed, resolve it, then push.
Report exact check results — never resolve on a failing or incomplete fix.

### 4. Wait for Codex to re-review

After a push, Codex re-reviews the new commit. Poll for a **new** Codex review whose
`commit_id` matches the just-pushed head (use ScheduleWakeup, ~120–270s between polls;
Codex typically responds within a few minutes). When the new review arrives, go to
step 1 for the next round.

## Stop conditions

Stop the loop and report when any of these is true:

- **Thumbs-up reaction** — the PR has a 👍 reaction from any reviewer. This signals
  all feedback is resolved and the human is satisfied. Done immediately: no need to
  wait for a new Codex review round. Summarize and exit.
- **Clean** — Codex's newest review on the current head approves or has zero
  actionable comments. Done: summarize rounds and the final state.
- **All remaining items pushed back** — nothing left to fix, only threads awaiting
  the reviewer/human. Post a summary of each push-back and **wait for the human**;
  do not resolve pushed-back threads or force the PR forward.
- **Blocked** — a fix can't be completed (failing check you can't resolve, ambiguous
  request, needs a decision). Report it and wait.

Check for 👍 reactions on the PR **before** polling for a new Codex review round.
If present, stop immediately — do not push or open more threads.

Never loop on push-backs: a pushed-back item only advances when a human responds.
Never guess Codex's verdict — read the actual latest review before deciding clean.

## Completion summary

Report: PR + final head commit; number of rounds; per round fixed/pushed-back counts;
final state (clean / awaiting-human / blocked); and every open push-back with its
reasoning so the human can decide.
