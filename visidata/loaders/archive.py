import codecs
import tarfile
import zipfile

from visidata import *


class ArchiveSheet(Sheet):
    'Provide wrapper around `zipfile` and `tarfile` libraries for opening archive files.'
    rowtype = 'files' # rowdef ZipInfo or TarInfo

    def __init__(self, p, archive_type='zip'):
        super().__init__(p.name, source=p)
        self.archive_type = archive_type

    @asyncthread
    def reload(self):

        if self.archive_type == 'zip':
            self.columns = [
                ColumnAttr('filename'),
                ColumnAttr('file_size', type=int),
                Column('date_time', type=date,
                       getter=lambda col, row: datetime.datetime(*row.date_time)),
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

        self.recalc()
        if self.archive_type == 'zip':
            contents = zipfile.ZipFile(self.source.resolve(), 'r').infolist()

        if self.archive_type == 'tar':
            contents = tarfile.open(name=self.source.resolve()).getmembers()

        for row in Progress(contents):
            self.addRow(row)

        self.recalc()

    def open_archive_file(self, fi):

        if self.archive_type == 'zip':
            zfp = zipfile.ZipFile(self.source.resolve(), 'r')
            decodedfp = codecs.iterdecode(zfp.open(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return openSource(PathFd(fi.filename, decodedfp, fi.file_size))

        if self.archive_type == 'tar':
            tfp = tarfile.open(name=self.source.resolve())
            decodedfp = codecs.iterdecode(tfp.extractfile(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return openSource(PathFd(fi.name, decodedfp, fi.size))

ArchiveSheet.addCommand(ENTER, 'dive-row', 'vd.push(open_archive_file(cursorRow))')
ArchiveSheet.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows: vd.push(open_archive_file(r))')

def open_zip(p):
    return ArchiveSheet(p, archive_type='zip')


def open_tar(p):
    return ArchiveSheet(p, archive_type='tar')

open_tgz = open_tar
open_txz = open_tar
open_tbz2 = open_tar
