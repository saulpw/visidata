- we are going to go from Path -> pathlib
- first order of business, what does visidata's path.py do?

## identical in both pathlib.Path and in vd.Path
- read_text
- is_dir
- parts
- parent
- exists
- with_name
- joinpath

## very similar (but minorly semantically different)
-__lt__
    - ours goes based off of the fn alone, theirs uses cparts 
- name, fn
    - in vd.Path, fn is the filename while `name` is minus the ext
    - in pathlib.Path `name` is the filename (incl ext), `stem` is minus the ext
- ext, compression, suffix
    - vd.Path has a concept of ext (all of a files extensions), compression (just the compression ext), suffix (ext - compression)
    - pathlib.Path has a property suffixes which has a list of the path's file extensions
- suffix
    - in pathlib.Path this is the file extension of the final component (.gz, .tsv, etc)
    - in vd.Path() we distinguish compression (.gz, etc) from suffix (.html, .tsv, etc)
- iterdir
    - vd.Path.iterdir returns a list and pathlib.Path.iterdir returns a generator
- open()
    - switch our internal calls to open() to super().open()
- whenever there is an os.path.blah(path.resolve()) in our code atm, it can be changed to os.path.blah(path) or os.blah(path)
    - `os` automatically handles Path-like objects in 3.6+
- vd.Path.resolve()
    - resolves from path object to string
    - the equivalent in pathlib.Path would be str(pathlib.Path())
    - pathlib.Path has a resolve() which does something completely different
- abspath
    - wrapper for os.path.abspath
    - pathlib.Path has resolve() (different from our resolve())
- relpath
    - wrapper for os.path.relpath
    - pathlib.Path has relative_to(), which is similar, but it has some different semantics (not an equiv substitute)
- __str__
    - does not return the abspath
        - in pathlib.Path, this returns the abspath
    - gives back what it originally got in visidata
    - might be tricky to adjust

## similar, but we have a wrapper that adds some functionality
- stat
    - performs a stat system call on a file (os.stat)
        - modification time and filesize
    - pathlib.Path has Path.stat(), Path.owner() and Path.group() - so we can get similar things, but we may want to swap os.stat for super.stat() but keep our wrapper
- vd.Path.`_open()`
    - handles uncompressing before passing to pathlib.Path.open()

## missing in pathlib.Path
- fqpn
- open_text (default mode = 'rt')
    - checks if the fqpn is stdin/stdout or a file
        - if stdin/stdout, super().open()
        - if file, self._open()
- vd.Path.__iter__()
    - incorporates Progress() tracking into file reading
- vd.Path.open_bytes
    - adds 'b' to the mode before passing to _open()
    - pathlib.Path has read_bytes() but not open_bytes()
- filesize
    - nada in pathlib.Path
- mtime
    - nada
