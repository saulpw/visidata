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

from dataclasses import dataclass

import sys
import io
import time
import zlib
import struct
import fnmatch

import urllib3

__version__ = '0.3'


def error(s):
    raise Exception(s)


@dataclass
class RemoteZipInfo:
    filename:str = ''
    date_time:int = 0
    header_offset:int = 0
    compress_type:int = 0
    compress_size:int = 0
    file_size:int = 0

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

    def infoiter(self):
        resp = self.http.request('HEAD', self.url)
        r = resp.headers.get('Accept-Ranges', '')
        if r != 'bytes':
            error(f"Accept-Ranges header must be 'bytes' ('{r}')")

        self.zip_size = int(resp.headers['Content-Length'])
        resp = self.get_range(self.zip_size-65536, 65536)

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

        filehdr_index = 65536 - (self.zip_size - cdir_start)
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
            return RemoteZipStream(resp, f)
        else:
            error(f'unknown compression method {method}')

    def open_text(self, fn):
        return io.TextIOWrapper(io.BufferedReader(self.open(fn)))


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
