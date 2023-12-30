# vgit

## latest version: v0.2-dev (2018-12-xx)

vgit is a [VisiData package](https://visidata.org) that provides a sleek terminal user interface to git, supplanting the arcana of git command-line operations with intuitive keystroke commands.

Current features include:
- viewing, stashing, staging, unstaging, and committing of diff hunks.
- viewing the git log (history)
- branch and remotes management
- branch merges and commit cherry-picks
- popping, applying, and dropping of stashed diffs
- setting of local and global git config options

## Installing vgit

vgit is located as a module within the [VisiData repo](https://github.com/saulpw/visidata/tree/develop/visidata/apps/vgit). It has its own setup.py. Note that installing vgit will also install VisiData.

```
pip install git+https://github.com/saulpw/visidata.git@branch#subdirectory=visidata/apps/vgit
```

### Dependencies

- Python 3.8+
- [VisiData](https://visidata.org/)
- [sh](https://github.com/saulpw/sh)

## Running vgit

`vgit [<working_dir>]` automatically opens a git status [sheet](https://www.visidata.org/docs/api/sheets#sheets) if the directory has a `.git` subdirectory.

Further documentation is available [here](vgit-guide.md).

## License

vgit is released under a GPLv3 license.
