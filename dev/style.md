# mandatory for functionality

- set global sheets on vd via `@VisiData.lazy_property`
   - otherwise they will not have full Sheet functionality from extensions
- set other global vars on vd directly at module-level
- add functions to vd with @VisiData.api or @VisiData.property

# Style Conventions

- camelCaps for "execstr" API (for commands and expressions)
- `under_score` for internal public API (can be used by other scripts)
- `_preunder` for internal private API (should not be used by outside scripts (no api guarantee))
- `single` for common things that can be used in either execstr or internally (like status and error)

- All VisiData functions in the API are available on the vd object, whose members are available in globals for execstr and internally.
- commands that reference a row or col should be on Sheet (not global or BaseSheet)


- Method names with leading underscore are private to file.
- Method names with embedded underscore are private but available to visidata internals.
- Method names without underscores (usually camelCase) are public API.
- Most strings in vd are single-quoted; within an *execstr*, inner strings are double-quoted.  This style is preferred to backslash escaping quotes: ``'foo("inner")'`` vs ``'foo(\'inner\')'``

# docs

- use "Ctrl+H" (titlecase Ctrl, plus sign, uppercase letter) instead of "^H"
- for commands, when space is not constrained, indicate the keystroke and add the longname in parens following the keystrokes.

# helpstrings

- `Ctrl+X` to perform action

 where "perform action" is the literal command helpstr.

# issues

For bugs that have a Github issue number, include the bug number on the same line as the primary fix, with two spaces before the `#` and no spaces after (like `break  #1234`).  We've started doing this for PRs also.  It's a bit of clutter but I'd like to see the code littered with these tiny notations of the bugfixes, so we can see at a glance where the battle scars are, and to avoid regressions if the function ever gets rewritten.

Any issue numbers fixed in a commit should also be appended to the git commit summary line, including the leading `#`.

## commit style

Most existing commits only have a compact one-line summary, and this is fine.
Additional information in the body is welcomed, in proportion to the time and complexity of the implementation (and especially for one-line bugfixes that a deceptive amount of effort).

Subject lines should generally fit under 50 characters but it's not rigidly enforced; it's better to have a clearer message at the cost of a few overflow characters.

Most commit messages should look like:

    [graph-] fix graph ranges for xmax, ymax < 1  #1673 #1697

The trailing `-` is for cases when the entire commit is safe and/or desirable to take in a patch release--tightly constrained and the code afterwards is unilaterally improved.
When we put together a patch release, we scan commit messages for this marker to see which ones should be included.
Ideally only and all `-` marked commits since the last release, would be in a patch release.

The tag should be the module name if the commit is focused on a particular module.
These tags are also used for code that doesn't affect functionality directly:

* `docs` for documentation-only commits
* `tests` for test-only commits (test framework and core tests)
* `dev` for non-code commits that are still relevant to development: release notes, packaging, git/github configuration, CI, file renames, etc.
* `api` for deliberate or sweeping changes to the API
* `www` for changes that only update the website
* `nfc`: guaranteed non-functional changes not in one of the above categories

For brevity, don't use generic verbs like `fix` or `use` (and especially not `utilize`), and don't repeat the module name in the summary.

In general:
   - commits should be rebased instead of merged, for a more linear and less cluttered commit log
   - try to squash features into a single commit (but don't over-squash either)
