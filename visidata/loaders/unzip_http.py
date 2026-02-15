#!/usr/bin/env python3

# Copyright (c) 2022 Saul Pwanson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
usage: unzip_http [-h] [-l] [-f] [-o] url [files ...]

Extract individual files from .zip files over http without downloading the
entire archive. HTTP server must send `Accept-Ranges: bytes` and
`Content-Length` in headers.

positional arguments:
  url                   URL of the remote zip file
  files                 Files to extract. If no filenames given, displays .zip
                        contents (filenames and sizes). Each filename can be a
                        wildcard glob.

options:
  -h, --help            show this help message and exit
  -l, --list            List files in the remote zip file
  -f, --full-filepaths  Recreate folder structure from zip file when extracting
                        (instead of extracting the files to the current
                        directory)
  -o, --stdout          Write files to stdout (if multiple files: concatenate
                        them to stdout, in zipfile order)
"""

import sys
import os
import io
import math
import time
import zlib
import struct
import fnmatch
import argparse
import pathlib
import urllib.parse


__version__ = '0.6'


def error(s):
    raise Exception(s)

def warning(s):
    print(s, file=sys.stderr)

def get_bits(val:int, *args):
    'Generate bitfields (one for each arg) from LSB to MSB.'
    for n in args:
        x = val & (2**n-1)
        val >>= n
        yield x


class RemoteZipInfo:
    def __init__(self, filename:str='',
                       date_time:int = 0,
                       header_offset:int = 0,
                       compress_type:int = 0,
                       compress_size:int = 0,
                       file_size:int = 0):
        self.filename = filename
        self.header_offset = header_offset
        self.compress_type = compress_type
        self.compress_size = compress_size
        self.file_size = file_size

        sec, mins, hour, day, mon, year = get_bits(date_time, 5, 6, 5, 5, 4, 7)
        self.date_time = (year+1980, mon, day, hour, mins, sec)

    def is_dir(self):
        return self.filename.endswith('/')

    def parse_extra(self, extra):
        i = 0
        while i < len(extra):
            fieldid, fieldsz = struct.unpack_from('<HH', extra, i)
            i += 4

            if fieldid == 0x0001:  # ZIP64
                if fieldsz == 8: fmt = '<Q'
                elif fieldsz == 16: fmt = '<QQ'
                elif fieldsz == 24: fmt = '<QQQ'
                elif fieldsz == 28: fmt = '<QQQI'

                vals = list(struct.unpack_from(fmt, extra, i))
                if self.file_size == 0xffffffff:
                    self.file_size = vals.pop(0)

                if self.compress_size == 0xffffffff:
                    self.compress_size = vals.pop(0)

                if self.header_offset == 0xffffffff:
                    self.header_offset = vals.pop(0)

            i += fieldsz


class RemoteZipFile:
    fmt_eocd = '<IHHHHIIH'  # end of central directory
    fmt_eocd64 = '<IQHHIIQQQQ'  # end of central directory ZIP64
    fmt_cdirentry = '<IHHHHIIIIHHHHHII'  # central directory entry
    fmt_localhdr = '<IHHHIIIIHH'  # local directory header
    magic_eocd64 = b'\x50\x4b\x06\x06'
    magic_eocd = b'\x50\x4b\x05\x06'

    def __init__(self, url):
        import urllib3
        self.url = url
        self.http = urllib3.PoolManager()
        self.zip_size = 0

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        pass

    @property
    def files(self):
        if not hasattr(self, '_files'):
            self._files = {r.filename:r for r in self.infoiter()}
        return self._files

    def infolist(self):
        return list(self.infoiter())

    def namelist(self):
        return list(r.filename for r in self.infoiter())

    def infoiter(self):
        resp = self.http.request('HEAD', self.url)
        r = resp.headers.get('Accept-Ranges', '')
        if r != 'bytes':
            hostname = urllib.parse.urlparse(self.url).netloc
            warning(f"{hostname} Accept-Ranges header ('{r}') is not 'bytes'--trying anyway")

        self.zip_size = int(resp.headers['Content-Length'])
        resp = self.get_range(
            max(self.zip_size-65536, 0),
            65536
        )

        cdir_start = -1
        i = resp.data.rfind(self.magic_eocd64)
        if i >= 0:
            magic, eocd_sz, create_ver, min_ver, disk_num, disk_start, disk_num_records, total_num_records, \
                cdir_bytes, cdir_start = struct.unpack_from(self.fmt_eocd64, resp.data, offset=i)
        else:
            i = resp.data.rfind(self.magic_eocd)
            if i >= 0:
                magic, \
                    disk_num, disk_start, disk_num_records, total_num_records, \
                    cdir_bytes, cdir_start, comment_len = struct.unpack_from(self.fmt_eocd, resp.data, offset=i)

        if cdir_start < 0 or cdir_start >= self.zip_size:
            error('cannot find central directory')

        if self.zip_size <= 65536:
            filehdr_index = cdir_start
        else:
            filehdr_index = 65536 - (self.zip_size - cdir_start)

        if filehdr_index < 0:
            resp = self.get_range(cdir_start, self.zip_size - cdir_start)
            filehdr_index = 0

        cdir_end = filehdr_index + cdir_bytes
        while filehdr_index < cdir_end:
            sizeof_cdirentry = struct.calcsize(self.fmt_cdirentry)

            magic, ver, ver_needed, flags, method, date_time, crc, \
                complen, uncomplen, fnlen, extralen, commentlen, \
                disknum_start, internal_attr, external_attr, local_header_ofs = \
                    struct.unpack_from(self.fmt_cdirentry, resp.data, offset=filehdr_index)

            filehdr_index += sizeof_cdirentry

            filename = resp.data[filehdr_index:filehdr_index+fnlen]
            filehdr_index += fnlen

            extra = resp.data[filehdr_index:filehdr_index+extralen]
            filehdr_index += extralen

            comment = resp.data[filehdr_index:filehdr_index+commentlen]
            filehdr_index += commentlen

            rzi = RemoteZipInfo(filename.decode(), date_time, local_header_ofs, method, complen, uncomplen)

            rzi.parse_extra(extra)
            yield rzi

    def extract(self, member, path=None, pwd=None):
            if pwd:
                raise NotImplementedError('Passwords not supported yet')

            path = path or pathlib.Path('.')

            outpath = path/member
            os.makedirs(outpath.parent, exist_ok=True)
            with self.open(member) as fpin:
                with open(path/member, mode='wb') as fpout:
                    while True:
                        r = fpin.read(65536)
                        if not r:
                            break
                        fpout.write(r)

    def extractall(self, path=None, members=None, pwd=None):
        for fn in members or self.namelist():
            self.extract(fn, path, pwd=pwd)

    def get_range(self, start, n):
        return self.http.request('GET', self.url, headers={'Range': f'bytes={start}-{start+n-1}'}, preload_content=False)

    def matching_files(self, *globs):
        for f in self.files.values():
            if any(fnmatch.fnmatch(f.filename, g) for g in globs):
                yield f

    def open(self, fn):
        if isinstance(fn, str):
            f = list(self.matching_files(fn))
            if not f:
                error(f'no files matching {fn}')
            f = f[0]
        else:
            f = fn

        sizeof_localhdr = struct.calcsize(self.fmt_localhdr)
        r = self.get_range(f.header_offset, sizeof_localhdr)
        localhdr = struct.unpack_from(self.fmt_localhdr, r.data)
        magic, ver, flags, method, dos_datetime, _, _, uncomplen, fnlen, extralen = localhdr
        if method == 0: # none
            return self.get_range(f.header_offset + sizeof_localhdr + fnlen + extralen, f.compress_size)
        elif method == 8: # DEFLATE
            resp = self.get_range(f.header_offset + sizeof_localhdr + fnlen + extralen, f.compress_size)
            return io.BufferedReader(RemoteZipStream(resp, f))
        else:
            error(f'unknown compression method {method}')

    def open_text(self, fn):
        return io.TextIOWrapper(self.open(fn))


class RemoteZipStream(io.RawIOBase):
    def __init__(self, fp, info):
        super().__init__()
        self.raw = fp
        self._decompressor = zlib.decompressobj(-15)
        self._buffer = bytes()

    def readable(self):
        return True

    def readinto(self, b):
        r = self.read(len(b))
        b[:len(r)] = r
        return len(r)

    def read(self, n):
        while n > len(self._buffer):
            r = self.raw.read(2**18)
            if not r:
                self._buffer += self._decompressor.flush()
                break
            self._buffer += self._decompressor.decompress(r)

        ret = self._buffer[:n]
        self._buffer = self._buffer[n:]

        return ret


 ### script start

class StreamProgress:
    def __init__(self, fp, name='', total=0):
        self.name = name
        self.fp = fp
        self.total = total
        self.start_time = time.time()
        self.last_update = 0
        self.amtread = 0

    def read(self, n):
        r = self.fp.read(n)
        self.amtread += len(r)
        now = time.time()
        if now - self.last_update > 0.1:
            self.last_update = now

            elapsed_s = now - self.start_time
            sys.stderr.write(f'\r{elapsed_s:.0f}s  {self.amtread/10**6:.02f}/{self.total/10**6:.02f}MB  ({self.amtread/10**6/elapsed_s:.02f} MB/s)  {self.name}')

        if not r:
            sys.stderr.write('\n')

        return r


def list_files(rzf):
    def safelog(x):
        return 1 if x == 0 else math.ceil(math.log10(x))

    digits_compr = max(safelog(f.compress_size) for f in rzf.infolist())
    digits_plain = max(safelog(f.file_size    ) for f in rzf.infolist())
    fmtstr = f'%{digits_compr}d -> %{digits_plain}d\t%s'
    for f in rzf.infolist():
        print(fmtstr % (f.compress_size, f.file_size, f.filename), file=sys.stderr)


def extract_one(outfile, rzf, f, ofname):
    print(f'Extracting {f.filename} to {ofname}...', file=sys.stderr)

    fp = StreamProgress(rzf.open(f), name=f.filename, total=f.compress_size)
    while r := fp.read(2**18):
        outfile.write(r)


def download_file(f, rzf, args):
    if not any(fnmatch.fnmatch(f.filename, g) for g in args.files):
        return

    if args.stdout:
        extract_one(sys.stdout.buffer, rzf, f, "stdout")
    else:
        path = pathlib.Path(f.filename)
        if args.full_filepaths:
            path.parent.mkdir(parents=True, exist_ok=True)
        else:
            path = path.name

        with open(str(path), 'wb') as of:
            extract_one(of, rzf, f, str(path))


def main():
    parser = argparse.ArgumentParser(prog='unzip-http', \
        description="Extract individual files from .zip files over http without downloading the entire archive. HTTP server must send `Accept-Ranges: bytes` and `Content-Length` in headers.")

    parser.add_argument('-l', '--list', action='store_true', default=False,
                        help="List files in the remote zip file")
    parser.add_argument('-f', '--full-filepaths', action='store_true', default=False,
                        help="Recreate folder structure from zip file when extracting (instead of extracting the files to the current directory)")
    parser.add_argument('-o', '--stdout', action='store_true', default=False,
                        help="Write files to stdout (if multiple files: concatenate them to stdout, in zipfile order)")

    parser.add_argument("url", nargs=1, help="URL of the remote zip file")
    parser.add_argument("files", nargs='*', help="Files to extract. If no filenames given, displays .zip contents (filenames and sizes). Each filename can be a wildcard glob.")

    args = parser.parse_args()

    rzf = RemoteZipFile(args.url[0])
    if args.list or len(args.files) == 0:
        list_files(rzf)
    else:
        for f in rzf.infolist():
            download_file(f, rzf, args)



if __name__ == '__main__':
    main()
