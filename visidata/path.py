import os
import os.path
import sys
import io
import codecs
import pathlib
from urllib.parse import urlparse, urlunparse
from functools import wraps, lru_cache

from visidata import vd
from visidata import VisiData, Progress

vd.help_encoding = '''Common Encodings:

- `utf-8`: Unicode (ASCII compatible, most common)
- `utf-8-sig`: Unicode as above, but saves/skips leading BOM
- `ascii`: 7-bit ASCII
- `latin1`: also known as `iso-8859-1`
- `cp437`: original IBM PC character set
- `shift_jis`: Japanese

See [:onclick https://docs.python.org/3/library/codecs.html#standard-encodings]https://docs.python.org/3/library/codecs.html#standard-encodings[/]
'''

vd.help_encoding_errors = '''Encoding Error Handlers:

- `strict`: raise error
- `ignore`: discard
- `replace`: replacement marker
- `backslashreplace`: use "\\uxxxxxx"
- `surrogateescape`: use surrogate characters

See [:onclick https://docs.python.org/3/library/codecs.html#error-handlers]https://docs.python.org/3/library/codecs.html#error-handlers[/]
'''

vd.option('encoding', 'utf-8-sig', 'encoding passed to codecs.open when reading a file', replay=True, help=vd.help_encoding)
vd.option('encoding_errors', 'surrogateescape', 'encoding_errors passed to codecs.open', replay=True, help=vd.help_encoding_errors)

@VisiData.api
def pkg_resources_files(vd, package):
    '''
    Returns a Traversable object (Path-like), based on the location of the package.
    importlib.resources.files exists in Python >= 3.9; use importlib_resources for the rest.
    '''
    try:
        from importlib.resources import files
    except ImportError: #1968
        from importlib_resources import files
    return files(package)

@lru_cache()
def vstat(path, force=False):
    try:
        return os.stat(path)
    except Exception as e:
        return None

def filesize(path):
    if hasattr(path, 'filesize') and path.filesize is not None:
        return path.filesize
    if hasattr(path, 'is_url') and path.is_url():
        return 0
    if hasattr(path, 'has_fp') and path.has_fp():
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
        self.encoding = encoding or text_io_buffer.encoding or vd.options.encoding
        self.errors = errors or text_io_buffer.errors or vd.options.encoding_errors

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
        self.fp_orig_readline = self.fp.readline
        self.fp_orig_close = self.fp.close

        self.fp.read = self.read
        self.fp.close = self.close

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

    def readline(self, size=-1):
        r = self.fp_orig_readline(size)
        if self.prog:
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

    @property
    def name(self):
        'Filename without any extensions.  Not the same as pathlib.Path.'
        return self.base_stem

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
            self.base_stem = self._path.name[:-len(self.suffix)]
        elif self._given == '.':  #1768
            self.base_stem = self._path.absolute().name
        else:
            self.base_stem = self._path.name

        # check if file is compressed
        if self.suffix in ['.gz', '.bz2', '.xz', '.lzma', '.zst']:
            self.compression = self.ext
            uncompressedpath = Path(self.given[:-len(self.suffix)])  # strip suffix
            self.base_stem = uncompressedpath.base_stem
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
        if isinstance(a, Path):
            return self._path.__lt__(a._path)
        return self._path.__lt__(a)

    def __truediv__(self, a):
        return Path(self._path.__truediv__(a))

    def has_fp(self):
        'Return True if this is a virtual Path to an already open file.'
        return bool(self.fp or self.fptext)

    def open(self, mode='rt', encoding=None, encoding_errors=None, newline=None):
        if 'b' in mode:
            return self.open_bytes(mode)

        return self.open_text(mode=mode, encoding=encoding, encoding_errors=encoding_errors, newline=newline)

    def open_bytes(self, mode='rb'):
        'Open the file pointed by this path and return a file object in binary mode.'
        if self.rfile:
            raise ValueError('a RepeatFile holds text and cannot be reopened in binary mode')

        if 'b' not in mode:
            mode += 'b'

        if self.given == '-':
            if 'r' in mode:
                return os.fdopen(vd._stdin.fileno(), 'rb')
            elif 'w' in mode or 'a' in mode:
                # convert 'a' to 'w' for stdout: https://bugs.python.org/issue27805
                return os.dup(vd._stdout.fileno())
            else:
                vd.error('invalid mode "%s" for Path.open()' % mode)
                return sys.stderr

        return self._open(mode=mode)

    def open_text(self, mode='rt', encoding=None, encoding_errors=None, newline=None):
        'Open path in text mode, using options.encoding and options.encoding_errors.  Return open file-pointer or file-pointer-like.'
        # rfile makes a single-access fp reusable

        if 't' not in mode:
            mode += 't'

        if self.rfile:
            return self.rfile.reopen()

        if self.fp and not self.fptext:
            self.fptext = codecs.iterdecode(self.fp,
                                            encoding=encoding or vd.options.encoding,
                                            errors=encoding_errors or vd.options.encoding_errors)

        if self.fptext:
            self.rfile = RepeatFile(self.fptext)
            return self.rfile

        if self.given == '-':
            if 'r' in mode:
                return vd._stdin
            elif 'w' in mode or 'a' in mode:
                # convert 'a' to 'w' for stdout: https://bugs.python.org/issue27805
                return open(os.dup(vd._stdout.fileno()), 'wt')
            else:
                vd.error('invalid mode "%s" for Path.open()' % mode)
                return sys.stderr

        return self._open(mode=mode, encoding=encoding or vd.options.encoding, errors=vd.options.encoding_errors, newline=newline)

    @wraps(pathlib.Path.read_text)
    def read_text(self, *args, **kwargs):
        'Open the file in text mode and return its entire decoded contents.'
        if 'encoding' not in kwargs:
            kwargs['encoding'] = vd.options.encoding
        if 'errors' not in kwargs:
            kwargs['errors'] = kwargs.get('encoding_errors', vd.options.encoding_errors)

        if self.lines:
            return RepeatFile(self.lines).read()
        elif self.fp:
            return self.fp.read()
        elif self.fptext:
            return self.fptext.read()
        else:
            return self._path.read_text(*args, **kwargs)

    @wraps(pathlib.Path.open)
    def _open(self, *args, **kwargs):
        if self.fp:
            return FileProgress(self, fp=self.fp, **kwargs)

        if self.fptext:
            return FileProgress(self, fp=BytesIOWrapper(self.fptext), **kwargs)

        path = self

        if self.compression == 'gz':
            import gzip
            zopen = gzip.open
        elif self.compression == 'bz2':
            import bz2
            zopen = bz2.open
        elif self.compression in ['xz', 'lzma']:
            import lzma
            zopen = lzma.open
        elif self.compression == 'zst':
            zstandard = vd.importExternal('zstandard')
            zopen = zstandard.open
        else:
            return FileProgress(path, fp=self._path.open(*args, **kwargs), **kwargs)

        if 'w' in kwargs.get('mode', ''):
            #1159 FileProgress on the outside to close properly when writing
            return FileProgress(path, fp=zopen(path, **kwargs), **kwargs)

        #1255 FileProgress on the inside to track uncompressed bytes when reading
        return zopen(FileProgress(path, fp=open(path, mode='rb'), **kwargs), **kwargs)

    def __iter__(self):
        with Progress(total=filesize(self)) as prog:
            with self.open(encoding=vd.options.encoding) as fd:
                for i, line in enumerate(fd):
                    prog.addProgress(len(line))
                    yield line.rstrip('\n')

    def read_bytes(self):
        'Return the entire binary contents of the pointed-to file as a bytes object.'
        with self.open(mode='rb') as fp:
            return fp.read()

    @wraps(pathlib.Path.is_fifo)
    def is_fifo(self):
        'Return True if the path is a fifo.'
        return self._path.is_fifo()

    def is_local(self):
        'Return True if self.filename refers to a file on the local disk.'
        return not bool(self.is_url()) and not bool(self.fp) and not bool(self.fptext)

    def is_url(self):
        'Return True if the given path appears to be a URL.'
        return '://' in self.given

    def __str__(self):
        if self.is_url():
            return self.given
        return str(self._path)

    @wraps(pathlib.Path.stat)
    @lru_cache()
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
            urlparts[2] = '/'.join(list(Path(urlparts[2]).parts[1:-1]) + [name])
            return Path(urlunparse(urlparts))
        else:
            return Path(self._from_parsed_parts(self._drv, self._root, list(self.parts[:-1]) + [name]))


class RepeatFile:
    '''Lazy file-like object that can be read and line-seeked more than once from memory.'''

    def __init__(self, iter_lines, lines=None):
        self.iter_lines = iter_lines
        self.lines = lines if lines is not None else []
        self.iter = RepeatFileIter(self)

    def __enter__(self):
        '''Returns a new independent file-like object, sharing the same line cache.'''
        return self.reopen()

    def __exit__(self, a,b,c):
        pass

    def reopen(self):
        'Return copy of file-like with internal iterator reset.'
        return RepeatFile(self.iter_lines, lines=self.lines)

    def read(self, n=None):
        '''Returns a string or bytes object. Unlike the standard read() function, when *n* is given, more than *n* characters/bytes can be returned, and often will.'''
        if n is None:
            n = 10**12  # some too huge number
        r = []
        size = 0
        output_type = str; eol = '\n'; joiner = ''
        while not r or size < n:
            try:
                s = next(self.iter)
                if not r and isinstance(s, bytes):
                    output_type = bytes; eol = b'\n'; joiner = b''
                assert isinstance(s, output_type), (s, output_type)
                r.append(s)
                r.append(eol)
                size += len(s) + len(eol)
            except StopIteration:
                break  # end of file
        return joiner.join(r)

    def write(self, s):
        return self.iter_lines.write(s)

    def tell(self):
        '''Tells the current position as an opaque line marker.'''
        return self.iter.nextIndex

    def seek(self, offset, whence=io.SEEK_SET):
        '''Seek to an already seen opaque line position marker only.'''
        if whence != io.SEEK_SET and offset != 0:
            if whence == io.SEEK_CUR:
                raise io.UnsupportedOperation("can't do nonzero cur-relative seeks")
            elif whence == io.SEEK_END:
                raise io.UnsupportedOperation("can't do nonzero end-relative seeks")
            else:
                raise ValueError('invalid whence (%s, should be %s, %s or %s)' % (whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END))
        self.iter.nextIndex = offset

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


vd.addGlobals(RepeatFile=RepeatFile,
              Path=Path,
              modtime=modtime,
              filesize=filesize,
              vstat=vstat)
