# User Documentation for vgit


## Global Keystrokes
- `H` opens the git log sheet (history) for the current branch
- `B` opens the git branches sheet
- `R` opens the remotes sheet
- `T` opens the stashes sheet
- `O` opens the git options sheet
- `X` opens the list of git commands executed
- `P`ushes the local refs to the currently set remote refs (`git push`)
- `Ctrl-s` stashes all uncommited changes (`git stash`)
- `Ctrl-p` pops the most recent stashed change and drops it (`git stash pop`)
- `A` aborts the cherry-pick/rebase/merge in-progress action shown on status line
- `L` opens the git blame sheet

## Git Status Sheet
- provides information about the working tree
- `a` stages a file for addition; `ga` stages all selected files for addition
- `m` renames a file
- `d` stages a file for deletion; `gd` stages all selected files for deletion
- `r` unstages a file
- `c` checks out a file
- `C` commits all staged changes
- `ENTER` pushes a hunks sheet for a file; `g<ENTER>` pushes hunks sheet for selected files (or all files, if none selected)
- `g/` performs a search through all files
- `x` executes an arbitrary git command
- `f` adds a --force flag to the next git command
- `i` adds a file to toplevel .gitignore; `gi` to add an input line to toplevel .gitignore
- `V` opens selected file
- `z<ENTER>` pushes hunks sheet for the staged diffs for the selected file; `zg<ENTER>` pushes hunks sheet for the staged diffs for selected files (or all files, if none selected)

## Hunks Sheet 
- opens a view for the hunks of a file (pieces of diffs)
- `ENTER` on a hunk shows you its diffs; `gENTER` scrolls through diffs for all of the selected hunks (or all hunks, if none selected)
- `a` stages a hunk
- `d` or `r` undoes this hunk
- `V` views the raw patch for this hunk

## Diff Viewer for Selected Hunks Sheet
- opens a view for the diff of a hunk
- `y`, `a` or `2` stages a hunk to the index and move on to the next hunk
- `r` or `1` removes this hunk from the diff (from the working tree)
- `n` or `<ENTER>` skips this hunk without staging 
- `d` deletes a line from a patch
- viewer exits when all hunks have been added or skipped

## Git Log Sheet (`H`istory)
- shows the git commit history for the selected branch
- `<ENTER>` shows the diff for the selected commit
- `c` cherry-picks the selected commit onto the current branch

## Git `B`ranches Sheet
- displays information about branches and enables their modification
- `a` creates a new branch
- `c` checks out a branch
- `d` removes a branch
- `e` renames a branch
- `<ENTER>` pushes the log sheet of the selected branch
- `m` merges the selected branch into the current branch

## Git `R`emotes Sheet
- for viewing and managing of remote urls
- `d` deletes a remote
- `a` adds a new remote

## Git S`T`ashes Sheet
- allows viewing of current stashed commits
- `<ENTER>` shows the selected stashed change
- `a` applies a stashed change without removing it from the stash
- `Ctrl-p` applies a stashed change and drops it
- `d`rops a stashed change
- `b` creates a new branch from the stashed change

## Git `O`ptions Sheet
- to view and/or edit git configuration (local/global/system)
- `a`dd new option
- `d` unsets this config value
- `gd` unsets all selected config values
- `e` edits an option; `ge` edits this option for all selected rows
