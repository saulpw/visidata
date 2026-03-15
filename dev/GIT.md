# Git and Version Control Practices

This document covers VisiData's conventions for Git commits, issue tracking, and version control workflow.

## Commit Message Style

Most existing commits only have a compact one-line summary, and this is fine. Additional information in the body is welcomed, in proportion to the time and complexity of the implementation (and especially for one-line bugfixes that took a deceptive amount of effort).

Subject lines should generally fit under 50 characters but it's not rigidly enforced. It's better to have a clearer message at the cost of a few overflow characters.

### Commit Message Format

Most commit messages should look like:

```
[graph-] fix graph ranges for xmax, ymax < 1  #1673 #1697
```

### Components

#### Tag (module name or category)
The tag in brackets should be the module name if the commit is focused on a particular module.

Special tags for non-functional changes:
- **`docs`** - Documentation-only commits
- **`tests`** - Test-only commits (test framework and core tests)
- **`dev`** - Non-code commits relevant to development: release notes, packaging, git/github configuration, CI, file renames, etc.
- **`nfc`** - Guaranteed non-functional changes not in the above categories

Other tags:
- **`api`** - Deliberate, breaking, or sweeping changes to the API

#### Trailing Dash (patch-safe marker)
The trailing `-` is for cases when the entire commit is safe and/or desirable to take in a patch release:
- Tightly constrained changes
- Code is unilaterally improved afterwards

When we put together a patch release, we scan commit messages for this marker to see which ones should be included. Ideally only and all `-` marked commits since the last release would be in a patch release.

Do not assume a commit is patch-safe — always ask before adding the `-` marker.

#### Issue Numbers
Any issue numbers fixed in a commit should be appended to the git commit summary line, including the leading `#`.

Examples:
- `#1234` - Single issue
- `#1673 #1697` - Multiple issues

### Writing Style

For brevity:
- Don't use generic verbs like `fix` or `use` (and especially not `utilize`)
- Don't repeat the module name in the summary

### Examples

```
[graph-] fix ranges for xmax, ymax < 1  #1673 #1697
[docs] update installation instructions
[tests-] add test for empty column handling  #2101
[daw] better interface for g( and x/y
[api] change Column.getValue signature
```

## Issue Tracking in Code

For bugs that have a Github issue number, include the bug number on the same line as the primary fix, with two spaces before the `#` and no spaces after:

```python
break  #1234
return None  #2567
```

We've started doing this for PRs also. It's a bit of clutter but it helps:
- See at a glance where the battle scars are in the code
- Avoid regressions if the function ever gets rewritten
- Track which issues resulted in actual code changes

## GitHub Comments and Replies

Commit before posting GitHub comments/replies. Let Saul push first, then post the comment. Don't post replies to issues before the relevant code is committed and pushed.

AI-generated comments should have the full attribution at the bottom: `[this message written by Claude Opus 4.6 and approved by @saulpw]`.

### Closing Issues for Implemented Features

When closing an issue for a feature that's already been implemented, the comment should include:
- A link to the implementing commit(s)
- Links to relevant documentation pages
- A brief example of how to use the feature (matching the original request if possible)
- Label wishlist issues with `wish granted` when closing

## Branch and Merge Workflow

In general:
- Commits should be **rebased** instead of merged, for a more linear and less cluttered commit log
- Try to **squash features** into a single commit (but don't over-squash either)
- Keep the commit history clean and meaningful

### Default Branch for Commits

By default, commit to **develop** unless explicitly working in another branch on a PR. If on a different branch, cherry-pick or switch to develop first.

### Pull Requests

`develop` is the trunk branch. PRs come from side branches, not from develop directly. Create a feature branch off develop for PRs.

Run `dev/test-all.sh` locally before pushing. After creating a PR, check CI status with `gh pr checks` and fix any failures before moving on.

### Documentation

Update docs in the same commit as the code change, not as a separate follow-up commit. Check `docs/README.md` for which files to update.

### Bug Fix PRs

Always add a regression test for bug fix PRs. Generate the golden output with the fix applied, and verify the test fails without the fix and passes with it.

### Wishlist items

- For external wishlist items, implement → PR → tag requester to verify.
