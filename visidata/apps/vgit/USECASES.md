
For each use case:

a) get it working
b) add menu items
c) help string for all sheets and columns and options and commands
d) test case
e) screenshot
f) brag tweet

# 0. vgit passthrough

+ any unknown command just acts exactly like git

# 1. vgit grep

+ launches vd interface to list of all matches 
+ can press Ctrl+O to open file at that location.
- g Enter to launch vim/$EDITOR with hotlist

# 3. vgit config

- add new config value
+ edit config value
+ unset config value


# 2. vgit branch

+ view branches incl metadata (last commit)
- checkout branch
- create branch
- delete branch
- rename branch
- go to log

# 4. vgit log

- freq on contributor
  - sum on nlines diff
- show commit
- cherry-pick to current branch
- reset to this commit
- checkout this commit
- revert commit
- drop commit and rebase
- copy SHA to system clipboard

- edit commit message like vgit amend

# 5. vgit blame
+ basic sheet
- combo with vgit grep somehow?

# 6. vgit stash

- view/apply/pop a specific stash item
- change stash item message
- see stash in sidebar as scrolling by
- create new branch from stashed change?

# 7. toplevel `g Ctrl+?` to reset current checkout to known state
- branch HEAD
- no diffs in any files
- not merging, not fixing conflicts
- not bisecting, etc

# 8. vgit status

- move files between staging/unstaged
- delete file 'd'
- rename file 'd'
- drop changes 'zd'
- see diff hunks for one/selected files
- zCtrl+S -> commit changes
- remove ignore-file and ignore-wildcard
- edit file

# 9. vgit repos

+ show all repos at a glance

# 10. vgit remote

+ add remote
+ delete remote
+ rename remote
+ edit remote url

# 10. vgit amend

- edit file, add hunk to much older commit
  - or commit message
- rebase later commits on top of new/old commit
- warn if already pushed
- test for various starting states, that all else gets saved/restored properly

# 11. vgit diff

+ git diff hunks
- show diff between committed, staged, unstaged
+ add/remove hunks in staged/unstaged
- diff between two commits

# . wow

- find all commits that added/changed only one line of code
   - and that have "#1234" in the commit message
- append appropriate "#1234" to each line of code
- see list of diffs
- commit

# schedule for removal

- vgit merge

# testing vgit

- have test repo with basic content
- do vgit commands
  - for some, check that contents of repo are correct (external fs state)
  - for others, check that output of last sheet is correct (internal vd state)

# needed visidata features

- rebind key on some sheets without unbinding it for the rest of visidata

