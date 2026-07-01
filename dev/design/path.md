# visidata.Path

- contains pathlib.Path as `._path` member
   -  `__getattr__` forwards to `.path` so interfaces are very similar
   - therefore .suffix same as pathlib.Path.suffix

Additions to pathlib.Path:

- .ext: file extension without leading '.' and without compression ext
- .compression: compression extension
- .given: the path as given (previously `fqpn` in vd 1.x)
- .open_text() (default mode = 'rt')
   - encoding/encoding_errors passed automatically from options
   - special-case if given file is '-' (stdin/stdout)
- .open_bytes() (pathlib.Path has read_bytes() but not open_bytes())
    - adds 'b' to the mode before passing to _open()
- vd.Path.__iter__()
    - incorporates Progress() tracking into file reading
- `.base_stem`: filename *without* any extensions

Differences from pathlib.Path:
- visidata.Path.iterdir returns a list and pathlib.Path.iterdir returns a generator
- `visidata.Path._open()`
    - handles uncompressing before passing to pathlib.Path.open()

TODO:
- change DirSheet owner/group to Path.owner()/group()
- move __iter__ off visidata.Path into global function

---

## Comparison with pathlib.Path (Nov 2019)

### Identical in both pathlib.Path and visidata.Path
 - read_text
 - is_dir
 - parts
 - parent
 - exists
 - with_name
 - joinpath

### Very similar (minor semantic differences)
 - `__lt__`: ours goes based off of the fn alone, theirs uses cparts
 - `name`/`fn`: in vd.Path, fn is the filename while `name` is minus the ext; in pathlib.Path `name` is the filename (incl ext), `stem` is minus the ext
 - `ext`/`compression`/`suffix`: vd.Path has ext (all extensions), compression (just compression ext), suffix (ext - compression); pathlib.Path has suffixes (list of extensions)
 - `suffix`: in pathlib.Path this is the file extension of the final component (.gz, .tsv, etc); in vd.Path we distinguish compression (.gz, etc) from suffix (.html, .tsv, etc)
 - `iterdir`: vd.Path.iterdir returns a list; pathlib.Path.iterdir returns a generator
 - `open()`: switch our internal calls to open() to super().open()
 - `os.path.blah(path.resolve())` in our code can be changed to `os.path.blah(path)` — `os` automatically handles Path-like objects in 3.6+
 - `resolve()`: vd.Path.resolve() resolves from path object to string; the equivalent in pathlib.Path would be str(pathlib.Path()); pathlib.Path.resolve() does something completely different
 - `abspath`: wrapper for os.path.abspath; pathlib.Path has resolve() (different from our resolve())
 - `relpath`: wrapper for os.path.relpath; pathlib.Path has relative_to(), which has different semantics
 - `__str__`: vd.Path does not return the abspath (gives back what it originally got); pathlib.Path returns the abspath

### Similar, but our wrapper adds functionality
 - `stat`: performs os.stat for mtime and filesize; pathlib.Path has Path.stat(), Path.owner() and Path.group() — could swap os.stat for super().stat() but keep our wrapper
 - `_open()`: handles uncompressing before passing to pathlib.Path.open()
