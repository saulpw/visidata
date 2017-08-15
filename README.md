# vgit v0.2

vgit is a sleek terminal user interface for git, supplanting the arcana of git command-line operations with intuitive keystrokes. It was built using the [VisiData tui](https://github.com/saulpw/visidata/blob/stable/visidata/vd.py) as a platform.

Current features include:
- viewing, stashing, staging, unstaging, and committing of diff hunks.
- viewing the git log (history)
- branch and remotes management
- branch merges and commit cherry-picks
- popping, applying, and dropping of stashed diffs
- setting of local and global git config options


## Installing vgit

### using pypi

```
pip3 install vgit
```

### cloning from git

```
$ git clone https://github.com/saulpw/vgit.git
$ cd vgit
$ pip3 install -r requirements.txt
$ python setup.py install
```

### Dependencies

- Python 3.3+
- sh

## Running vgit

`vgit [<working_dir>]` opens a git status sheet for the given working directory (or the current directory if not specified).

Further documentation is available [here](vgit-guide.md).

## License

vgit is released under a GPLv3 license.

