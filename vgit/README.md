# vgit

## latest version: v0.3 (2018-12-xx)

vgit is a [VisiData plugin](https://visidata.org/plugins) that provides a sleek terminal user interface to git, supplanting the arcana of git command-line operations with intuitive keystroke commands.

Current features include:
- viewing, stashing, staging, unstaging, and committing of diff hunks.
- viewing the git log (history)
- branch and remotes management
- branch merges and commit cherry-picks
- popping, applying, and dropping of stashed diffs
- setting of local and global git config options

## Installing vgit

vgit comes installed with VisiData v1.6+, but it is not enabled by default.  To enable, add this line to your `$HOME/.visidatarc`:

        from vgit import open_dir

You may have to install the additional [requirements](plugins/vgit/requirements.txt)

### Dependencies

- Python 3.4+
- [VisiData](https://visidata.org/)
- [sh](https://amoffat.github.io/sh/)

## Running vgit

`vd [<working_dir>]` automatically opens a git status sheet if the directory has a `.git` subdirectory.

Further documentation is available [here](vgit-guide.md).

## License

vgit is released under a GPLv3 license.
