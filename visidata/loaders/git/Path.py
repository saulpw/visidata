import os
import os.path
import gzip

from vdtui import *

option('skip', 0, 'skip first N lines of text input')

class Path:
    'File and path-handling class, modeled on `pathlib.Path`.'
    def __init__(self, fqpn):
        self.fqpn = fqpn
        fn = os.path.split(fqpn)[-1]

        # check if file is gzip-compressed
        if fn.endswith('.gz'):
            self.gzip_compressed = True
            fn = fn[:-3]
        else:
            self.gzip_compressed = False

        self.name, self.ext = os.path.splitext(fn)
        self.suffix = self.ext[1:]

    def open_text(self, mode='r'):
        if self.gzip_compressed:
            return gzip.open(self.resolve(), mode='rt', encoding=options.encoding, errors=options.encoding_errors)
        else:
            return open(self.resolve(), mode=mode, encoding=options.encoding, errors=options.encoding_errors)

    def __iter__(self):
        for i, line in enumerate(self.open_text()):
            if i < options.skip:
                continue
            yield line[:-1]

    def read_text(self):
        with self.open_text() as fp:
            return fp.read()

    def read_bytes(self):
        with open(self.resolve(), 'rb') as fp:
            return fp.read()

    def is_dir(self):
        return os.path.isdir(self.resolve())

    def exists(self):
        return os.path.exists(self.resolve())

    def iterdir(self):
        return [self.parent] + [Path(os.path.join(self.fqpn, f)) for f in os.listdir(self.resolve())]

    def stat(self):
        try:
            return os.stat(self.resolve())
        except:
            return None

    def resolve(self):
        'Resolve pathname shell variables and ~userdir'
        return os.path.expandvars(os.path.expanduser(self.fqpn))

    def relpath(self, start):
        return os.path.relpath(os.path.realpath(self.resolve()), start)

    @property
    def parent(self):
        'Return Path to parent directory.'
        return Path(self.fqpn + "/..")

    @property
    def filesize(self):
        return self.stat().st_size

    def __str__(self):
        return self.fqpn

class UrlPath:
    def __init__(self, url):
        from urllib.parse import urlparse
        self.url = url
        self.obj = urlparse(url)
        self.name = self.obj.netloc

    def __str__(self):
        return self.url

    def __getattr__(self, k):
        return getattr(self.obj, k)


class PathFd(Path):
    'minimal Path interface to satisfy a tsv loader'
    def __init__(self, pathname, fp, filesize=0):
        super().__init__(pathname)
        self.fp = fp
        self.alreadyRead = []  # shared among all RepeatFile instances
        self._filesize = filesize

    def read_text(self):
        return self.fp.read()

    def open_text(self):
        return RepeatFile(self)

    @property
    def filesize(self):
        return self._filesize


class RepeatFile:
    def __init__(self, pathfd):
        self.pathfd = pathfd
        self.iter = None

    def __enter__(self):
        self.iter = RepeatFileIter(self)
        return self

    def __exit__(self, a,b,c):
        pass

    def seek(self, n):
        assert n == 0, 'RepeatFile can only seek to beginning'
        self.iter = RepeatFileIter(self)

    def __iter__(self):
        return RepeatFileIter(self)

    def __next__(self):
        return next(self.iter)

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

