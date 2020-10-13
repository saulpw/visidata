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

Differences from pathlib.Path:
- `.name`: filename *without* extension
   - TODO: change uses of Path.name to Path.stem
- visidata.Path.iterdir returns a list and pathlib.Path.iterdir returns a generator
- `visidata.Path._open()`
    - handles uncompressing before passing to pathlib.Path.open()

TODO:
- pathlib.Path has a property suffixes which has a list of the path's file extensions
- change DirSheet owner/group to Path.owner()/group()
- move __iter__ off visidata.Path into global function
