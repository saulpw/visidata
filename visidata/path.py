import os
import os.path
import sys
import io
import codecs
import pathlib
from urllib.parse import urlparse, urlunparse
from functools import wraps

from visidata import *

vd.option('encoding', 'utf-8', 'encoding passed to codecs.open', replay=True)
vd.option('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open', replay=True)

@functools.lru_cache()
def vstat(path, force=False):
    try:
        return os.stat(path)
    except Exception as e:
        return None

def filesize(path):
    if hasattr(path, 'filesize') and path.filesize is not None:
        return path.filesize
    if path.has_fp() or path.is_url():
        return 0
    st = path.stat() # vstat(path)
    return st and st.st_size

def modtime(path):
    st = path.stat()
    return st and st.st_mtime


# from https://stackoverflow.com/questions/55889474/convert-io-stringio-to-io-bytesio
class BytesIOWrapper(io.BufferedReader):
    """Wrap a buffered bytes stream over TextIOBase string stream."""

    def __init__(self, text_io_buffer, encoding=None, errors=None, **kwargs):
        super(BytesIOWrapper, self).__init__(text_io_buffer, **kwargs)
        self.encoding = encoding or text_io_buffer.encoding or options.encoding
        self.errors = errors or text_io_buffer.errors or options.encoding_errors

    def _encoding_call(self, method_name, *args, **kwargs):
        raw_method = getattr(self.raw, method_name)
        val = raw_method(*args, **kwargs)
        return val.encode(self.encoding, errors=self.errors)

    def read(self, size=-1):
        return self._encoding_call('read', size)

    def read1(self, size=-1):
        return self._encoding_call('read1', size)

    def peek(self, size=-1):
        return self._encoding_call('peek', size)


class FileProgress:
    'Open file in binary mode and track read() progress.'
    def __init__(self, path, fp, mode='r', **kwargs):
        self.path = path
        self.fp = fp
        self.prog = None
        if 'r' in mode:
            gerund = 'reading'
            self.prog = Progress(gerund=gerund, total=filesize(path))
        elif 'w' in mode:
            gerund = 'writing'
            self.prog = Progress(gerund=gerund)
        else:
            gerund = 'nothing'

        # track Progress on original fp
        self.fp_orig_read = self.fp.read
        self.fp_orig_close = self.fp.close
        # These two lines result in bug #1159, a corrupted save of corruption formats
        # for now we are reverting by commenting out, and opened #1175 to investigate
        # Progress bars for compression formats might not work in the meanwhile
        #self.fp.read = self.read
        #self.fp.close = self.close

        if self.prog:
            self.prog.__enter__()

    def close(self, *args, **kwargs):
        if self.prog:
            self.prog.__exit__(None, None, None)
            self.prog = None
        return self.fp_orig_close(*args, **kwargs)

    def read(self, size=-1):
        r = self.fp_orig_read(size)
        if self.prog:
            if r:
                self.prog.addProgress(len(r))
        return r

    def __getattr__(self, k):
        return getattr(self.fp, k)

    def __enter__(self):
        self.fp.__enter__()
        return self

    def __next__(self):
        r = next(self.fp)
        self.prog.addProgress(len(r))
        return r

    def __iter__(self):
        if not self.prog:
            yield from self.fp
        else:
            for line in self.fp:
                self.prog.addProgress(len(line))
                yield line

    def __exit__(self, type, value, tb):
        return self.fp.__exit__(type, value, tb)


class Path(os.PathLike):
    'File and path-handling class, modeled on `pathlib.Path`.'
    def __init__(self, given, fp=None, fptext=None, lines=None, filesize=None):
        # Resolve pathname shell variables and ~userdir
        self.given = os.path.expandvars(os.path.expanduser(str(given)))
        self.fptext = fptext
        self.fp = fp
        self.lines = lines or []  # shared among all RepeatFile instances
        self.filesize = filesize
        self.rfile = None

    @functools.lru_cache()
    def stat(self, force=False):
        return self._path.stat()

    @property
    def given(self):
        'The path as given to the constructor.'
        return self._given

    @given.setter
    def given(self, given):
        self._given = given
        if isinstance(given, os.PathLike):
            self._path = given
        else:
            self._path = pathlib.Path(given)

        self.ext = self.suffix[1:]
        if self.suffix:  #1450  don't make this a oneliner; [:-0] doesn't work
            self.name = self._path.name[:-len(self.suffix)]
        else:
            self.name = self._path.name

        # check if file is compressed
        if self.suffix in ['.gz', '.bz2', '.xz', '.lzma', '.zst']:
            self.compression = self.ext
            uncompressedpath = Path(self.given[:-len(self.suffix)])  # strip suffix
            self.name = uncompressedpath.name
            self.ext = uncompressedpath.ext
        else:
            self.compression = None

    def __getattr__(self, k):
        if hasattr(self.__dict__, k):
            r = getattr(self.__dict__, k)
        else:
            if self.__dict__.get('_path', None) is not None:
                r = getattr(self._path, k)
            else:
                raise AttributeError(k)
        if isinstance(r, pathlib.Path):
            return Path(r)
        return r

    def __fspath__(self):
        return self._path.__fspath__()

    def __lt__(self, a):
        if isinstance(a, visidata.Path):
            return self._path.__lt__(a._path)
        return self._path.__lt__(a)

    def __truediv__(self, a):
        return Path(self._path.__truediv__(a))

    def has_fp(self):
        'Return True if this is a virtual Path to an already open file.'
        return bool(self.fp or self.fptext)

    def open_text(self, mode='rt', encoding=None, encoding_errors=None, newline=None):
        'Open path in text mode, using options.encoding and options.encoding_errors.  Return open file-pointer or file-pointer-like.'
        # rfile makes a single-access fp reusable

        if self.rfile:
            return self.rfile

        if self.fp:
            self.fptext = codecs.iterdecode(self.fp,
                                            encoding=encoding or options.encoding,
                                            errors=encoding_errors or options.encoding_errors)

        if self.fptext:
            self.rfile = RepeatFile(self.fptext)
            return self.rfile

        if 't' not in mode:
            mode += 't'

        if self.given == '-':
            if 'r' in mode:
                return vd._stdin
            elif 'w' in mode or 'a' in mode:
                # convert 'a' to 'w' for stdout: https://bugs.python.org/issue27805
                return open(os.dup(vd._stdout.fileno()), 'wt')
            else:
                vd.error('invalid mode "%s" for Path.open_text()' % mode)
                return sys.stderr

        return self.open(mode=mode, encoding=encoding or vd.options.encoding, errors=vd.options.encoding_errors, newline=newline)

    @wraps(pathlib.Path.read_text)
    def read_text(self, *args, **kwargs):
        'Open the file in text mode and return its entire decoded contents.'
        if 'encoding' not in kwargs:
            kwargs['encoding'] = options.encoding
        if 'errors' not in kwargs:
            kwargs['errors'] = kwargs.get('encoding_errors', options.encoding_errors)

        if self.lines:
            return RepeatFile(self.lines).read()
        elif self.fp:
            return self.fp.read()
        else:
            return self._path.read_text(*args, **kwargs)

    @wraps(pathlib.Path.open)
    def open(self, *args, **kwargs):
        if self.fp:
            return FileProgress(self, fp=self.fp, **kwargs)

        if self.fptext:
            return FileProgress(self, fp=BytesIOWrapper(self.fptext), **kwargs)

        path = self
        binmode = 'wb' if 'w' in kwargs.get('mode', '') else 'rb'
        if self.compression == 'gz':
            import gzip
            return gzip.open(FileProgress(path, fp=open(path, mode=binmode), **kwargs), *args, **kwargs)
        elif self.compression == 'bz2':
            import bz2
            return bz2.open(FileProgress(path, fp=open(path, mode=binmode), **kwargs), *args, **kwargs)
        elif self.compression in ['xz', 'lzma']:
            import lzma
            return lzma.open(FileProgress(path, fp=open(path, mode=binmode), **kwargs), *args, **kwargs)
        elif self.compression == 'zst':
            import zstandard
            return zstandard.open(FileProgress(path, fp=open(path, mode=binmode), **kwargs), *args, **kwargs)
        else:
            return FileProgress(path, fp=self._path.open(*args, **kwargs), **kwargs)

    def __iter__(self):
        with Progress(total=filesize(self)) as prog:
            with self.open_text(encoding=vd.options.encoding) as fd:
                for i, line in enumerate(fd):
                    prog.addProgress(len(line))
                    yield line.rstrip('\n')

    def open_bytes(self, mode='rb'):
        'Open the file pointed by this path and return a file object in binary mode.'
        if 'b' not in mode:
            mode += 'b'
        return self.open(mode=mode)

    def read_bytes(self):
        'Return the entire binary contents of the pointed-to file as a bytes object.'
        with self.open(mode='rb') as fp:
            return fp.read()

    def is_url(self):
        'Return True if the given path appears to be a URL.'
        return '://' in self.given

    def __str__(self):
        if self.is_url():
            return self.given
        return str(self._path)

    @wraps(pathlib.Path.stat)
    @functools.lru_cache()
    def stat(self, force=False):
        'Return Path.stat() if relevant.'
        try:
            if not self.is_url():
                return self._path.stat()
        except Exception as e:
            return None

    @wraps(pathlib.Path.exists)
    def exists(self):
        'Return True if the path can be opened.'
        if self.has_fp() or self.is_url():
            return True
        return self._path.exists()

    @property
    def scheme(self):
        'The URL scheme component, if path is a URL.'
        if self.is_url():
            return urlparse(self.given).scheme

    def with_name(self, name):
        'Return a sibling Path with *name* as a filename in the same directory.'
        if self.is_url():
            urlparts = list(urlparse(self.given))
            urlparts[2] = '/'.join(Path(urlparts[2])._parts[1:-1] + [name])
            return Path(urlunparse(urlparts))
        else:
            return Path(self._from_parsed_parts(self._drv, self._root, self._parts[:-1] + [name]))


class RepeatFile:
    '''Lazy file-like object that can be read and line-seeked more than once from memory.'''

    def __init__(self, iter_lines, lines=None):
        self.iter_lines = iter_lines
        self.lines = lines if lines is not None else []
        self.iter = RepeatFileIter(self)

    def __enter__(self):
        '''Returns a new independent file-like object, sharing the same line cache.'''
        return RepeatFile(self.iter_lines, lines=self.lines)

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
            except StopIteration:
                break  # end of file
        return r

    def write(self, s):
        return self.iter_lines.write(s)

    def tell(self):
        '''Tells the current position as an opaque line marker.'''
        return self.iter.nextIndex

    def seek(self, n):
        '''Seek to an already seen opaque line position marker only.'''
        self.iter.nextIndex = n

    def readline(self, size=-1):
        if size != -1:
            vd.error('RepeatFile does not support limited line length')
        try:
            return next(self.iter)
        except StopIteration:
            return ''

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
        elif self.rf.iter_lines:
            try:
                r = next(self.rf.iter_lines)
                self.rf.lines.append(r)
            except StopIteration:
                self.rf.iter_lines = None
                raise
        else:
            raise StopIteration()


        self.nextIndex += 1
        return r
