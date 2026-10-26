# Review a guide

The reviewer half of [guide-prompt.md](guide-prompt.md).  Run it in a fresh agent that did not write the guide:

> Follow dev/guide-review.md to review visidata/guides/SaversGuide.md in wip/guide-SaversGuide.

---

Review the guide named in the request, as the maintainer reviewing its PR would.  Do not edit any files.  The output is a list of notes for the writer.

## Read first

- `dev/DOCS.md` (all of it, and especially "Guides") and `docs/api/style.rst`.
- The exemplar guides: `SortGuide.md`, `SelectionGuide.md`, `ColumnsGuide.md`, `ClipboardGuide.md`, `ErrorsSheet.md` in `visidata/guides/`.  They set length and density.  Where an exemplar breaks a rule, the rule wins.
- The guide's line in `guides_list` in `visidata/guide.py`, including any trailing `#` comment.
- The guide source, and its rendered text from `dev/guide-check.py -r <Name>`, run from the worktree.
- Notes from earlier rounds and how each was resolved, if the request includes them.  Do not reopen a resolved note without new evidence.

## Check

Work through each pass, and quote the line for every note (or the heading, for a note on a whole section or on something missing from it).  In every round, run every pass on the whole guide, not only the changes.  Topics the request says are pending a maintainer decision are not notes.

1. Sentences.  For each sentence outside a `{help...}` line, ask what a user loses if it is deleted.  If the heading or a helpstring in that section already says it, or it explains a general data concept, it is a note.
2. Rules.  Go through `dev/DOCS.md` and `docs/api/style.rst` rule by rule.  The usual misses are "VisiData" by name, second person, passive voice, "can"/"will"/"should", "Press", UI narration, hedging parentheticals, and caret notation.
3. Accuracy.  For every behavioral claim beyond a helpstring, read the implementation.  Run every example and example table in batch mode (`python3 -m visidata -b <file> -p <script.vdj> -o <path>` from the worktree, with every output path absolute in a fresh `mktemp -d`) and compare it cell by cell.  A `.vdx` script is one command per line, `longname input` separated by a space (see `dev/TESTING.md`).  A prompt with several fields (like save's path and filetype) needs a `.vdj` line with `"input": {...}`.  Always pass `-o`; without it batch mode dumps the sheet to stdout.  An overwrite confirmation aborts batch replay, so save to fresh paths.  For behavior only reachable interactively (prompt keys, sidebar), drive vd in tmux, as `tests/test-tui.sh` does.  In a prompt with a prefilled value, the first typed character replaces the whole value.  Verify independently; the PR body's list of what the writer verified is not evidence.  An unconfirmed claim is a note, and so is a simplification that makes a claim false.  Try to confirm the claims the PR body lists as unconfirmed.  A bug the PR body reports is not a note unless the guide states something it makes false in normal use.
4. Coverage.  Grep for the longnames and option names in the guide, and look through `addCommand`, `vd.option`, and `addMenuItems` in every module that defines them.  A command or option a regular user needs that is missing from the guide is a note, and so is a niche one taking space in it.  The PR body's "left out" list, if there is one, is the writer's case for each omission.  Judge it.
5. Density.  Compare length and the ratio of prose to list lines with the exemplars.  A section that reads like a tutorial is a note.
6. Rendering.  Read the rendered text top to bottom.  Notes cover a blank or raw `{...}` expansion, a helpstring that reads badly once expanded, a mid-sentence `{help...}`, a wrapped table, and anything confusing out of context.

## Output

One numbered list.  Each note starts with its severity, then the line (quoted), the problem, the rule or reason, and a concrete fix (replacement text, or "delete").  No praise, no summary.

- **blocker**: false, misleading, or missing something a regular user needs.
- **edit**: breaks a rule in `dev/DOCS.md` or `docs/api/style.rst`, or a maintainer would change it before merging.
- **nit**: a defensible preference.
- **helpstring**: wording style in an expanded helpstring (articles, terseness, consistency with neighbors).  These never send the guide back; the writer collects them in the PR body for a separate pass.  A helpstring that is wrong or unclear is a blocker or an edit.

If there is nothing to fix, the whole output is exactly:

    No notes.

Do not hold back a real note to reach "No notes", and do not mark a preference as an edit.
