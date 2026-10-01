---
name: update-github-actions-pinned-sha
description: Update GitHub Actions to use latest stable releases and pin action references to immutable commit SHAs. Use when working with .github/workflows/*.yml or .github/actions/.
---

# Skill: Update GitHub Actions to Latest Stable Pinned SHAs

## Purpose

Update GitHub Actions workflow dependencies to the latest stable versions and pin each versioned action to an immutable commit SHA.

This instruction is compatible with Codex, OpenCode, and Claude Code. Store it as `AGENTS.md`, `CLAUDE.md`, or a shared skill file and symlink/copy as needed.

## Scope

Review and update:

- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`
- `.github/actions/**/action.yml`
- `.github/actions/**/action.yaml`

Only update GitHub Actions `uses:` references. Do not change unrelated workflow logic.

## Core Rules

0. **Verify tool availability before relying on it.** If GitHub MCP or `gh`
   returns empty/error, fall back immediately to `git ls-remote`. Do not
   silently skip lookups.
1. Check the internet for every external action before updating it.
2. Prefer the latest stable release or stable semver tag.
3. Exclude prereleases unless the workflow already requires one.
4. Pin versioned actions to the exact commit SHA.
5. Add an inline comment showing the version that the SHA represents.
6. Keep `main` or `master` only when no stable versioned release/tag exists.
7. Preserve existing workflow behavior.

## Required Output Format

Use this format for pinned actions:

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

Use this format for branch-only actions:

```yaml
- uses: owner/action@main # no versioned release/tag available
```

Do not pin local actions:

```yaml
- uses: ./.github/actions/example
```

## Stable Version Selection

For each external action, choose the target ref in this order:

1. Latest non-prerelease GitHub Release
2. Latest stable semver tag
3. Latest documented stable major tag
4. `main` or `master` only when no versioned release/tag exists

Reject versions containing:

```text
alpha
beta
rc
preview
next
canary
nightly
dev
experimental
```

## Procedure

### 1. Find action references

```bash
grep -R "uses:" .github/workflows .github/actions 2>/dev/null || true
```

Classify each `uses:` entry:

- external action: `owner/repo@ref`
- reusable workflow: `owner/repo/.github/workflows/file.yml@ref`
- local action: `./path`
- Docker action: `docker://image:tag`

Only process external GitHub action and reusable workflow references.

### 2. Look up the latest stable version online

Use GitHub MCP tools first, then fall back to `git ls-remote` if needed.

**Step A — Try GitHub MCP (preferred):**

For each external action, use `github_get_latest_release` to get the latest
non-prerelease release tag:

```
github_get_latest_release owner=actions checkout
```

If no release exists, fall back to `github_list_tags` and filter for the
latest stable semver. Reject any tag containing:
`alpha`, `beta`, `rc`, `preview`, `next`, `canary`, `nightly`, `dev`, `experimental`.

```
github_list_tags owner=actions checkout per_page=100
```

Select the highest stable semver tag (e.g., `v4.2.2` over `v4.1.7`).

**Step B — Fall back to `git ls-remote` if MCP is unavailable:**

```bash
# List all tags (filtered client-side):
git ls-remote "https://github.com/owner/repo.git" | grep -E 'refs/tags/'
```

**Step C — Resolve the selected tag to a commit SHA:**

Use `github_get_tag` to get the target commit SHA directly:

```
github_get_tag owner=actions checkout tag="v4.2.2"
```

If `github_get_tag` fails, fall back to `git ls-remote`:

```bash
git ls-remote "https://github.com/owner/repo.git" "refs/tags/v4.2.2"
```

The output format is `<sha>    refs/tags/<tag>` — extract the SHA from the first field.

**Always verify results** — do not assume a known version or guess from memory.

### 4. Update workflow files

Replace version refs with resolved SHAs and add a version comment.

Before:

```yaml
- uses: actions/checkout@v4
```

After:

```yaml
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
```

For reusable workflows:

```yaml
uses: owner/repo/.github/workflows/ci.yml@<commit_sha> # v1.2.3
```

For branch-only actions:

```yaml
- uses: owner/action@main # no versioned release/tag available
```

Keep all existing `with:`, `env:`, `permissions:`, matrix, triggers, and job logic unchanged.

### 5. Record lookup notes

Add lookup notes to the PR body or task comment.

Use this table:

```markdown
| Action | Previous Ref | Latest Stable | Lookup Method | Resolved SHA | Decision |
| --- | --- | --- | --- | --- | --- |
| `actions/checkout` | `v4` | `v4.2.2` | github_get_latest_release | `11bd71901bbe5b1630ceea73d27597364c9af683` | pinned |
| `owner/action` | `main` | none | GitHub tags checked | n/a | kept branch |
```

### 6. Validate

Run YAML validation:

```bash
python - <<'PY'
from pathlib import Path
import yaml

paths = list(Path(".github/workflows").glob("*.yml")) + list(Path(".github/workflows").glob("*.yaml"))

for path in paths:
    with path.open("r", encoding="utf-8") as f:
        yaml.safe_load(f)
    print(f"OK: {path}")
PY
```

Review the diff:

```bash
git diff -- .github/workflows .github/actions
```

Confirm:

- every external action was checked online
- latest stable versions were selected
- every possible versioned action is pinned to SHA
- every SHA pin has a version comment
- branch-only actions have an explanation comment
- local actions were not changed
- no unrelated workflow logic changed

### 7. Commit

```bash
git add .github/workflows .github/actions
git commit -m "chore(ci): pin GitHub Actions to stable SHAs"
```

## PR Template

```markdown
## Summary

Updated GitHub Actions dependencies to latest stable versions and pinned versioned actions to immutable commit SHAs.

## Changes

- Checked GitHub releases/tags for each external action using GitHub MCP (github_get_latest_release, github_get_tag) with git ls-remote fallback
- Updated actions to latest stable versions
- Resolved selected tags to commit SHAs
- Added inline comments documenting the version behind each SHA
- Kept branch-only actions on `main`/`master` only when no versioned release/tag exists
- Preserved existing workflow behavior

## Lookup Notes

| Action | Previous Ref | Latest Stable | Lookup Method | Resolved SHA | Decision |
| --- | --- | --- | --- | --- | --- |
|  |  |  | |  |  |

## Validation

- [ ] Workflow YAML parses successfully
- [ ] Every external action was checked online
- [ ] Latest stable versions were selected
- [ ] Versioned actions are pinned to commit SHAs
- [ ] Each pinned SHA includes a version comment
- [ ] Branch-only actions include an explanation comment
- [ ] No unrelated CI logic changed
```

## Definition of Done

The task is done when:

- all external GitHub Actions references are reviewed
- every action has a fresh GitHub release/tag lookup
- latest stable versions are selected
- versioned actions are pinned to commit SHAs
- each SHA has an inline version comment
- branch-only actions are justified with comments
- YAML validation passes
- diff contains only intentional CI dependency updates
- PR includes lookup notes
