import codecs
import tarfile
import zipfile

from visidata import *


class read_archive(Sheet):
    'Provide wrapper around `zipfile` and `tarfile` libraries for opening archive files.'
    rowtype = 'files'

    def __init__(self, p, archive_type='zip'):
        super().__init__(p.name, source=p)
        self.archive_type = archive_type
        if self.archive_type == 'zip':
            self.columns = [
                ColumnAttr('filename'),
                ColumnAttr('file_size', type=int),
                Column('date_time', type=date, getter=lambda col, row: datetime.datetime(*row.date_time)),
                ColumnAttr('compress_size', type=int)
            ]
        if self.archive_type == 'tar':
            self.columns = [
                ColumnAttr('name'),
                ColumnAttr('size', type=int),
                ColumnAttr('mtime', type=date),
                ColumnAttr('type', type=int),
                ColumnAttr('mode', type=int),
                ColumnAttr('uname'),
                ColumnAttr('gname')
            ]

    def reload(self):
        if self.archive_type == 'zip':
            with zipfile.ZipFile(self.source.resolve(), 'r') as zfp:
                self.rows = zfp.infolist()

        if self.archive_type == 'tar':
            with tarfile.open(name=self.source.resolve()) as tfp:
                self.rows = tfp.getmembers()

    def openArchiveFileEntry(self, fi):
        if self.archive_type == 'zip':
            zfp = zipfile.ZipFile(self.source.resolve(), 'r')
            decodedfp = codecs.iterdecode(zfp.open(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            name = fi.filename
            size = fi.file_size

        if self.archive_type == 'tar':
            tfp = tarfile.open(name=self.source.resolve())
            decodedfp = codecs.iterdecode(tfp.extractfile(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            name = fi.name
            size = fi.size

        return openSource(PathFd(name, decodedfp, size))

read_archive.addCommand(ENTER, 'dive-row', 'vd.push(openArchiveFileEntry(cursorRow))')
read_archive.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(openArchiveFileEntry(r))')

def open_zip(p):
    return read_archive(p, archive_type='zip')


def open_tar(p):
    return read_archive(p, archive_type='tar')

open_tgz = open_tar
open_txz = open_tar
open_tbz2 = open_tar
