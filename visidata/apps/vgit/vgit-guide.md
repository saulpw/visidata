# User Documentation for vgit

## Global Commands

- `^S` to stash all uncommited changes (`git stash`)
- `^P` to pops the most recent stashed change and drops it (`git stash pop`)
- `A` to abort the cherry-pick/rebase/merge in-progress action shown on status line

- `f` is for force, to prefix any command


###

- `a` is for add, to stage the current row in the index
- `b` is for branch, to start a new branch
- `c` is for checkout, to update the working tree with the current row
- `d` is for delete, to remove the current row
- `e` is for the builtin editor, to change the current cell
- `r` is for reset, to unstage the current row from the index
- `Shift-E` is for your own $EDITOR, to change the current row
- `Shift-C` is for commit, from the index to the repo

The exact command(s) required in each case are context dependent.
A `g` prefix will make the command affect all selected rows instead.  If no rows are selected, it will fanout to all rows.
For example, 'ge' edits the current cell, then sets the current column for all selected rows to the same value.

### Commands that push or change sheets are always shift-keystrokes.

- `H` History (`git log`)
- `B` Branches (`git branch`)
- `R` Remotes (`git remote`)
- `O` Options (`git config`)
- `T` sTashes (`git stash`)
- `L` bLame (`git blame`)
- `G` Git command history

### Workflows

- checkout a commit: 'H'istory, choose commit, 'c'heckout
   - see contents of the commit first: ENTER for file listing, then ENTER for diff against parent.

- checkout a different branch: 'B'ranches, move cursor to desired branch, 'c'heckout

- amend an older commit with contents of the index: 'H'istory, choose commit, 'C'ommit; will confirm and then amend/rebase

- dig through code: b'L'ame, ENTER

- `P`ush the local refs to the currently set remote refs (`git push`)

- 


## Quick Reference

### Global Keystrokes
- `P`ushes the local refs to the currently set remote refs (`git push`)

### Git Status Sheet
- provides information about the working tree
- a/r/c/d should be intuitive
- `m` moves a file (or `e`dit the filename to rename within the current directory)_
- `Enter` pushes a hunks sheet for a file; `gEnter` pushes hunks sheet for selected files (or all files, if none selected)
- `g/` performs a search through all files
- `x` executes an arbitrary git command
- `f` adds a --force flag to the next git command
- `i` adds a file to toplevel .gitignore; `gi` to add an input line to toplevel .gitignore
- `Shift-V` opens selected file in $Editor
- `zEnter` opens hunks sheet for the staged diffs for the selected file; `gzEnter` pushes hunks sheet for the staged diffs for selected files (or all files, if none selected)

### Hunks Sheet 
- opens a view for the hunks of a file (pieces of diffs)
- `Enter` on a hunk shows you its diffs; `gEnter` scrolls through diffs for all of the selected hunks (or all hunks, if none selected)
- `a` stages a hunk
- `d` or `r` undoes this hunk
- `Shift-V` views the raw patch for this hunk

### Diff Viewer for Selected Hunks Sheet
- opens a view for the diff of a hunk
- `y`, `a` or `2` stages a hunk to the index and move on to the next hunk
- `r` or `1` removes this hunk from the diff (from the working tree)
- `n` or `<ENTER>` skips this hunk without staging 
- `d` deletes a line from a patch
- viewer exits when all hunks have been added or skipped

### Git Log Sheet (`H`istory)
- shows the git commit history for the selected branch
- `Enter` shows the diff for the selected commit
- `Shift-C` amends the selected commit to contain the currently staged changes
- `r` resets the shown branch HEAD to the selected commit
- `p` cherry-picks the selected commit onto the current branch

### Git `B`ranches Sheet
- displays information about branches and enables their modification
- `a` creates a new branch
- `c` checks out a branch
- `d` removes a branch
- `e` renames a branch
- 
- `Enter` pushes the log sheet of the selected branch
- `m` merges the selected branch into the current branch

### Git `R`emotes Sheet
    - for viewing and managing of remote urls
    - `d` deletes a remote
    - `a` adds a new remote

### Git S`T`ashes Sheet
    - allows viewing of current stashed commits
    - `<ENTER>` shows the selected stashed change
    - `a` applies a stashed change without removing it from the stash
    - `Ctrl-p` applies a stashed change and drops it
    - `d` drops a stashed change
    - `b` creates a new branch from the stashed change

## Git `O`ptions Sheet
    - to view and/or edit git configuration (local/global/system)
    - `a` adds new option
    - `d` unsets this config value
    - `gd` unsets all selected config values
    - `e` edits an option; `ge` edits this option for all selected rows
