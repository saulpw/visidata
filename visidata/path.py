import os
import os.path
import sys
import pathlib
from urllib.parse import urlparse, urlunparse

from visidata import *

option('encoding', 'utf-8', 'encoding passed to codecs.open', replay=True)
option('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open', replay=True)
option('skip', 0, 'skip first N lines of text input', replay=True)

@functools.lru_cache()
def vstat(path, force=False):
    try:
        return os.stat(path)
    except Exception as e:
        return None

def filesize(path):
    if hasattr(path, 'filesize') and path.filesize is not None:
        return path.filesize
    if path.fp or path.is_url():
        return 0
    st = path.stat() # vstat(path)
    return st and st.st_size

def modtime(path):
    st = path.stat()
    return st and st.st_mtime


class Path(os.PathLike):
    'File and path-handling class, modeled on `pathlib.Path`.'
    def __init__(self, given, fp=None, lines=None, filesize=None):
        # Resolve pathname shell variables and ~userdir
        self.given = os.path.expandvars(os.path.expanduser(given))
        self.fp = fp
        self.lines = lines or []  # shared among all RepeatFile instances
        self.filesize = filesize

    @functools.lru_cache()
    def stat(self, force=False):
        return self._path.stat()

    @property
    def given(self):
        return self._given

    @given.setter
    def given(self, given):
        self._given = given
        if isinstance(given, os.PathLike):
            self._path = given
        else:
            self._path = pathlib.Path(given)

        self.ext = self.suffix[1:]
        if self.suffix:
            self.name = self._path.name[:-len(self.suffix)]
        else:
            self.name = self._path.name

        # check if file is compressed
        if self.suffix in ['.gz', '.bz2', '.xz']:
            self.compression = self.ext
            uncompressedpath = Path(self.given[:-len(self.suffix)])
            self.name = uncompressedpath.name
            self.ext = uncompressedpath.ext
        else:
            self.compression = None

    def __getattr__(self, k):
        if hasattr(self.__dict__, k):
            r = getattr(self.__dict__, k)
        else:
            r = getattr(self._path, k)
        if isinstance(r, pathlib.Path):
            return Path(r)
        return r

    def __fspath__(self):
        return self._path.__fspath__()

    def __lt__(self, a):
        return self._path.__lt__(a)

    def __truediv__(self, a):
        return Path(self._path.__truediv__(a))

    def open_text(self, mode='rt'):
        if self.fp:
            return RepeatFile(fp=self.fp)

        if 't' not in mode:
            mode += 't'

        if self.given == '-':
            if 'r' in mode:
                return vd._stdin
            elif 'w' in mode or 'a' in mode:
                # convert 'a' to 'w' for stdout: https://bugs.python.org/issue27805
                return open(os.dup(vd._stdout.fileno()), 'wt')
            else:
                error('invalid mode "%s" for Path.open_text()' % mode)
                return sys.stderr

        return self.open(mode=mode, encoding=options.encoding, errors=options.encoding_errors)

    def read_text(self, *args):
        if self.lines:
            return RepeatFile(iter_lines=self.lines).read()
        elif self.fp:
            return self.fp.read()
        else:
            return self._path.read_text(*args)

    def open(self, *args, **kwargs):
        fn = self
        if self.compression == 'gz':
            import gzip
            return gzip.open(fn, *args, **kwargs)
        elif self.compression == 'bz2':
            import bz2
            return bz2.open(fn, *args, **kwargs)
        elif self.compression == 'xz':
            import lzma
            return lzma.open(fn, *args, **kwargs)
        else:
            return self._path.open(*args, **kwargs)

    def __iter__(self):
        skip = options.skip
        with Progress(total=filesize(self)) as prog:
            for i, line in enumerate(self.open_text()):
                prog.addProgress(len(line))
                if i < skip:
                    continue
                yield line[:-1]

    def open_bytes(self, mode='rb'):
        if 'b' not in mode:
            mode += 'b'
        return self.open(mode=mode)

    def read_bytes(self):
        with self.open(mode='rb') as fp:
            return fp.read()

    def is_url(self):
        return '://' in self.given

    def __str__(self):
        if self.is_url():
            return self.given
        return str(self._path)

    @functools.lru_cache()
    def stat(self, force=False):
        try:
            if not self.is_url():
                return self._path.stat()
        except Exception as e:
            return None

    def exists(self):
        if self.fp or self.is_url():
            return True
        return self._path.exists()

    @property
    def scheme(self):
        if self.is_url():
            return urlparse(self.given).scheme

    def with_name(self, name):
        if self.is_url():
            urlparts = list(urlparse(self.given))
            urlparts[2] = str(Path(urlparts[2]).with_name(name))
            return Path(urlunparse(urlparts))
        else:
            return self._path.with_name(name)


class RepeatFile:
    def __init__(self, *, fp=None, iter_lines=None):
        'Provide either fp or iter_lines, and lines will be filled from it.'
        self.fp = fp
        self.iter_lines = iter_lines
        self.lines = []
        self.iter = RepeatFileIter(self)

    def __enter__(self):
        self.iter = RepeatFileIter(self)
        return self

    def __exit__(self, a,b,c):
        pass

    def read(self, n=None):
        r = ''
        if n is None:
            n = 10**12  # some too huge number
        while len(r) < n:
            try:
                s = next(self.iter)
                r += s + '\n'
                n += len(r)
            except StopIteration:
                break  # end of file
        return r

    def seek(self, n):
        assert n == 0, 'RepeatFile can only seek to beginning'
        self.iter = RepeatFileIter(self)

    def __iter__(self):
        return RepeatFileIter(self)

    def __next__(self):
        return next(self.iter)

    def exists(self):
        return True


class RepeatFileIter:
    def __init__(self, rf):
        self.rf = rf
        self.nextIndex = 0

    def __iter__(self):
        return RepeatFileIter(self.rf)

    def __next__(self):
        if self.nextIndex < len(self.rf.lines):
            r = self.rf.lines[self.nextIndex]
        else:
            if self.rf.iter_lines:
                r = next(self.rf.iter_lines)
            elif self.rf.fp:
                r = next(self.rf.fp)
            self.rf.lines.append(r)

        self.nextIndex += 1
        return r

