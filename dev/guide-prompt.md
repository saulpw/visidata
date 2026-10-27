# Write a guide

The writer half of the process for adding one guide from the list in `visidata/guide.py` (tracked in #2313).  The reviewer half is [guide-review.md](guide-review.md).

## Process

The operator (a top-level session or a human) runs:

1. A writer agent: "Follow dev/guide-prompt.md to write the guide SaversGuide."  It stops at a committed local branch and a PR body file.
2. A fresh reviewer agent: "Follow dev/guide-review.md to review visidata/guides/SaversGuide.md in wip/guide-SaversGuide."  Name any topic pending a maintainer decision, so the reviewer skips it.
3. If any note is a blocker or an edit, send the notes to the writer, who applies each one or rebuts it in its report, commits, and updates the PR body.  Then go back to step 2 with a new reviewer, and give it every earlier round's notes with how each was resolved.  After three rounds that still have blockers or edits, stop and show the notes to Saul.
4. When a round has only nits, the writer lists them in the PR body under "Nits", and the operator pushes the branch and opens the PR from the PR body file.  (`gh pr edit` fails on a Projects-classic deprecation error; update a PR body with `gh api -X PATCH repos/saulpw/visidata/pulls/<n> -F body=@<file>`.)

Do not change `dev/DOCS.md`, this file, or `guide-review.md` during a run.  Process fixes go in between guides.

A note that the reviewer misses but a human catches belongs in `dev/DOCS.md` or `guide-review.md`, so the next run catches it.

---

Write the in-app guide named in the request.  Stop at a committed local branch.

## 0. Worktree

    git worktree add wip/guide-<Name> -b guide/<Name> develop

Do all the work there.  Run `python3 -m visidata` and `dev/guide-check.py` from the worktree, so they use its code.

## 1. Orient

Read these first:

- `CLAUDE.md`, `AGENTS.md`, `dev/DOCS.md` (especially "Guides"), `docs/api/style.rst`, `dev/GIT.md`, `dev/ai-levels.md`.
- `visidata/guide.py`: the guide's line in `guides_list` gives its title, and a trailing `#` comment there is part of the spec.
- Exemplar guides in `visidata/guides/`: `SortGuide.md`, `SelectionGuide.md`, `ColumnsGuide.md`, `ClipboardGuide.md`, `ErrorsSheet.md`.  Match their length and density.

Stop and report if `visidata/guides/<Name>.md` already exists, or if `gh pr list --state open --search <Name>` or the comments on #2313 (`gh api repos/saulpw/visidata/issues/2313/comments`) show someone else working on it.  An offer the maintainers declined does not count.

## 2. Inventory

Collect every candidate command and option for the topic before choosing any:

- `addCommand` calls and `addMenuItems` entries in the modules that implement the feature.  Find them by grepping for the topic's longnames and option names; a topic often spans several modules (saving touches `save.py`, `modify.py`, `main.py`, and the loaders).
- `vd.option` and `vd.theme_option` calls in those modules.
- The sidebar `guide` attribute on the relevant sheet class, if any.  The guide may go further than the sidebar, but must not contradict it.
- `docs/*.md` (see `docs/README.md`), the manpage source `visidata/man/vd.inc`, and `CHANGELOG.md` for recent changes.

Drop deprecated commands (`vd.deprecated`, `visidata/deprecated.py`), and commands that only repeat another with a trivial difference.  Choose the 5-15 commands and options a regular user reaches for.  Keep the rest in a list for the PR body, each with a one-line reason.

## 3. Verify

Do not describe behavior that has not been confirmed.  For anything the guide says beyond a helpstring (what `g` or `z` changes, interaction with selected rows, column types, undo, which sheet results land on), read the implementation, and run it in batch mode where possible:

    python3 -m visidata -b sample.csv -p script.vdj -o out.tsv

Use `sample_data/` and `tests/` for input files.  Make a fresh scratch directory (`mktemp -d`, or one inside a harness-provided scratchpad) and give every output path in it absolutely, so nothing lands in the worktree.  Generate every example table from a batch run; never write one by hand.  A `.vdx` script is one command per line, `longname input` separated by a space (see `dev/TESTING.md`).  A prompt with several fields (like save's path and filetype) needs a `.vdj` line with `"input": {...}`.  Always pass `-o`; without it batch mode dumps the sheet to stdout.  An overwrite confirmation aborts batch replay, so save to fresh paths.  For behavior only reachable interactively (prompt keys, sidebar), drive vd in tmux, as `tests/test-tui.sh` does.  In a prompt with a prefilled value, the first typed character replaces the whole value.

Fix errors found while verifying in docs (`docs/`), the manpage source (`visidata/man/vd.inc`), and helpstrings in this PR, each in its own commit tagged with its module (`[man]`, `[save]`), and list them in the PR body under "Fixed in this PR".  Do not fix code.  Report surprising code behavior in the PR body under "Possible bugs", as questions: some of it is intentional (`save-sheet-really` overwrites even under `--readonly`, like vim's `:w!`).  Describe the actual behavior in the guide, or leave the feature out.

## 4. Write

Create `visidata/guides/<Name>.md`, following the "Guides" section of `dev/DOCS.md`:

- `# Title` from `guides_list`, then at most one sentence before the first section.
- `## Section` headings are short noun phrases or bare imperatives.  Each section is 2-6 list lines (commands, options, or short facts), with at most one sentence of setup.
- `{help.commands.longname}` and `{help.options.name}` on their own list lines.
- Notes only where behavior is surprising or specific to VisiData.
- A topic driven mostly by CLI flags or options gets a section of hand-written list items in the same "`<flag>` to <do something>" form.  So does a key with no longname (like `Ctrl+Q`).
- Options last, under `## Options`.  A note on an option goes directly after the list.
- An `## Examples` section only when the effect of a command is not clear from its helpstring.
- Set `sheettype` front matter only when the commands live on a sheet type other than `Sheet`.
- Aim for 20-60 lines.

When an expanded helpstring reads badly (unclear, inconsistent with its neighbors, wrong), fix the helpstring in the source instead of writing the line out by hand.  Put helpstring changes in their own commit, tagged with the module and `#2313` (`[save] drop stray paren from save-all helpstring  #2313`), and run `dev/test-all.sh`, since goldens include help text.

## 5. Self-review

- `dev/guide-check.py <Name>` prints nothing.  Check only this guide; problems in other guides are out of scope.
- `dev/guide-check.py -r <Name>` renders the guide.  Read it all as a user would.
- For each sentence outside a `{help...}` line, ask what a user loses if it is deleted.  Delete it when the answer is "nothing the heading or a helpstring doesn't already say".
- Every section is mostly list lines: commands, options, or short facts.  Fold a prose-only section into a list, or merge it into the section it qualifies.
- Go through `dev/DOCS.md` rule by rule against the text.  Search the text for "VisiData", "you", "can ", "will ", "should ", and "Press".

## 6. Commit

Commit the guide as `[guides] add <Name>  #2313`.  On later rounds, add fixup commits on the branch, not amends.

Write the PR body to `wip/guide-<Name>.pr.md`, with:

- One line on what the guide covers.
- The commands and options included.
- The candidates left out, each with its reason.
- Anything unconfirmed or questionable.
- Fixed in this PR: doc, manpage, and helpstring errors.
- Possible bugs: surprising code behavior, as questions.
- Nits from the last review round, if any.
- Helpstring wording notes from every round, under "Helpstring wording", for a separate pass.
- `Part of #2313`.
- `AI Level: 8` with the model name, for an unattended run.  Saul sets the final level when he reviews.

Do not push, open a PR, edit the checklist on #2313, or comment anywhere.  The operator does those.

Report the branch, commit IDs, the PR body path, anything left unverified, and, on later rounds, how each review note was handled.
