import codecs
import tarfile
import zipfile
from visidata.loaders import unzip_http

from visidata import vd, VisiData, asyncthread, Sheet, Progress, Menu, options
from visidata import ColumnAttr, Column, date, datetime, Path

@VisiData.api
def open_zip(vd, p):
    return vd.ZipSheet(p.name, source=p)

@VisiData.api
def open_tar(vd, p):
    return TarSheet(p.name, source=p)

VisiData.open_tgz = VisiData.open_tar
VisiData.open_txz = VisiData.open_tar
VisiData.open_tbz2 = VisiData.open_tar

@VisiData.api
class ZipSheet(Sheet):
    'Wrapper for `zipfile` library.'
    rowtype = 'files' # rowdef [ZipInfo, zipfile.Path]
    columns = [
        Column('directory',
            getter=lambda col,row: str(row[1].parent) if str(row[1].parent) == '.' else str(row[1].parent) + '/'),
        Column('filename', getter=lambda col,row: row[1].name + row[1].suffix),
        Column('abspath', type=str, width=0, getter=lambda col,row: row[1]),
        Column('ext', getter=lambda col,row: row[0].filename.endswith('/') and '/' or row[1].ext),
        Column('size', getter=lambda col,row: row[0].file_size, type=int),
        Column('compressed_size', type=int, getter=lambda col,row: row[0].compress_size),
        Column('date_time', type=date,
               getter=lambda col, row: datetime.datetime(*row[0].date_time)),
    ]
    nKeys = 2

    def openZipFile(self, fp, *args, **kwargs):
        '''Use VisiData input to handle password-protected zip files.'''
        try:
            return fp.open(*args, **kwargs)
        except RuntimeError as err:
            if 'password required' in err.args[0]:
                pwd = vd.input(f'{args[0].filename} is encrypted, enter password: ', display=False)
                return fp.open(*args, **kwargs, pwd=pwd.encode('utf-8'))
            vd.error(err)

    def openRow(self, row):
            fi, zpath = row
            decodedfp = codecs.iterdecode(self.openZipFile(self.zfp, fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return vd.openSource(Path(fi.filename, fp=decodedfp, filesize=fi.file_size), filetype=options.filetype)

    @asyncthread
    def extract(self, *rows, path=None):
        for r, path in Progress(rows):
            self.zfp.extractall(members=[r.filename], path=path)
            vd.status(f'extracted {r.filename}')

    @property
    def zfp(self):
        if '://' in str(self.source):
            unzip_http.warning = vd.warning
            return unzip_http.RemoteZipFile(str(self.source))

        return zipfile.ZipFile(str(self.source), 'r')

    def iterload(self):
        with self.zfp as zf:
            for zi in Progress(zf.infolist()):
#                yield [zi, zipfile.Path(zf, at=zi.filename)]
                yield [zi, Path(zi.filename)]


class TarSheet(Sheet):
    'Wrapper for `tarfile` library.'
    rowtype = 'files' # rowdef TarInfo
    columns = [
        ColumnAttr('name'),
        ColumnAttr('size', type=int),
        ColumnAttr('mtime', type=date),
        ColumnAttr('type', type=int),
        ColumnAttr('mode', type=int),
        ColumnAttr('uname'),
        ColumnAttr('gname')
    ]

    def openRow(self, fi):
            tfp = tarfile.open(name=str(self.source))
            decodedfp = codecs.iterdecode(tfp.extractfile(fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return vd.openSource(Path(fi.name, fp=decodedfp, filesize=fi.size))

    def iterload(self):
        with tarfile.open(name=str(self.source)) as tf:
            for ti in Progress(tf.getmembers()):
                yield ti


ZipSheet.addCommand('x', 'extract-file', 'extract(cursorRow)', 'extract current file to current directory')
ZipSheet.addCommand('gx', 'extract-selected', 'extract(*onlySelectedRows)', 'extract selected files to current directory')
ZipSheet.addCommand('zx', 'extract-file-to', 'extract(cursorRow, path=inputPath("extract to: "))', 'extract current file to given pathname')
ZipSheet.addCommand('gzx', 'extract-selected-to', 'extract(*onlySelectedRows, path=inputPath("extract %d files to: " % nSelectedRows))', 'extract selected files to given directory')

vd.addMenu(Menu('File', Menu('Extract',
        Menu('current file', 'extract-file'),
        Menu('current file to', 'extract-file-to'),
        Menu('selected files', 'extract-selected'),
        Menu('selected files to', 'extract-selected-to'),
    )))

vd.addGlobals({
    'ZipSheet': ZipSheet,
    'TarSheet': TarSheet
})
