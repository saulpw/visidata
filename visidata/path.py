import os
import os.path
import sys
import pathlib

from visidata import *

option('encoding', 'utf-8', 'encoding passed to codecs.open', replay=True)
option('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open', replay=True)
option('skip', 0, 'skip first N lines of text input', replay=True)

@functools.lru_cache()
def vstat(path, force=False):
    try:
        return os.stat(path.resolve())
    except Exception as e:
        return None

def filesize(path):
    if hasattr(path, 'filesize'):
        return path.filesize
    st = vstat(path)
    return st and st.st_size

def modtime(path):
    st = path.stat()
    return st and st.st_mtime


class Path(os.PathLike):
    'File and path-handling class, modeled on `pathlib.Path`.'
    def __init__(self, given):
        # Resolve pathname shell variables and ~userdir
        self.given = os.path.expandvars(os.path.expanduser(given))

    @property
    def given(self):
        return self._given

    @given.setter
    def given(self, given):
        self._given = given
        self._path = pathlib.Path(given)

        self.ext = self.suffix[1:]
        self.name = self._path.name[:-len(self.suffix)]

        # check if file is compressed
        if self.suffix in ['.gz', '.bz2', '.xz']:
            self.compression = self.ext
            uncompressedpath = Path(self.given[:-len(self.suffix)])
            self.name = uncompressedpath.name
            self.ext = uncompressedpath.ext
        else:
            self.compression = None

        self._stat = None

    def __getattr__(self, k):
        if hasattr(self.__dict__, k):
            return getattr(self.__dict__, k)
        return getattr(self._path, k)

    def __fspath__(self):
        return self._path.__fspath__()

    def __lt__(self, a):
        return self._path.__lt__(a)

    def __truediv__(self, a):
        return Path(self._path.__truediv__(a))

    def open_text(self, mode='rt'):
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

    def open(self, *args, **kwargs):
        fn = self.resolve()
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

    def iterdir(self):
        return [Path(os.path.join(self.given, f)) for f in os.listdir(self.resolve())]

    def __str__(self):
        return str(self._path)


class UrlPath(Path):
    def __init__(self, url):
        from urllib.parse import urlparse
        self.url = url
        self.obj = urlparse(url)
        super().__init__(self.obj.path)

    def __str__(self):
        return self.url

    def __getattr__(self, k):
        if hasattr(self.obj, k):
            return getattr(self.obj, k)
        return super().__getattr__(k)

    def exists(self):
        return True

    def __str__(self):
        return self.given



class PathFd(Path):
    'minimal Path interface to satisfy a tsv loader'
    def __init__(self, pathname, fp, filesize=0):
        super().__init__(pathname)
        self.fp = fp
        self.alreadyRead = []  # shared among all RepeatFile instances
        self.filesize = filesize

    def read_text(self):
        return self.fp.read()

    def open_text(self):
        return RepeatFile(self)

    def exists(self):
        return True


class RepeatFile:
    def __init__(self, pathfd):
        self.pathfd = pathfd
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
        if self.nextIndex < len(self.rf.pathfd.alreadyRead):
            r = self.rf.pathfd.alreadyRead[self.nextIndex]
        else:
            r = next(self.rf.pathfd.fp)
            self.rf.pathfd.alreadyRead.append(r)

        self.nextIndex += 1
        return r

