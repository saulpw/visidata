import pathlib
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
VisiData.open_whl = VisiData.open_zip

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
            fp = self.openZipFile(self.zfp, fi)
            return vd.openSource(Path(fi.filename, fp=fp, filesize=fi.file_size), filetype=options.filetype)

    def extract(self, *rows, path=None):
        path = path or pathlib.Path('.')

        files = []
        for row in rows:
            r, _ = row
            if (path/r.filename).exists():
                vd.confirm(f'{r.filename} exists, overwrite? ')  #1452
            self.extract_async(row)

    @asyncthread
    def extract_async(self, *rows, path=None):
        'Extract rows to *path*, without confirmation.'
        for r, _ in Progress(rows):
            self.zfp.extract(member=r.filename, path=path)
            vd.status(f'extracted {r.filename}')

    @property
    def zfp(self):
        if not self._zfp:
            if '://' in str(self.source):
                unzip_http.warning = vd.warning
                self._zfp = unzip_http.RemoteZipFile(str(self.source))
            else:
                self._zfp = zipfile.ZipFile(str(self.source), 'r')

        return self._zfp

    def iterload(self):
        for zi in Progress(self.zfp.infolist()):
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
            return vd.openSource(Path(fi.name, fp=tfp.extractfile(fi), filesize=fi.size))

    def iterload(self):
        with tarfile.open(name=str(self.source)) as tf:
            for ti in Progress(tf.getmembers()):
                yield ti


ZipSheet.init('_zfp', lambda: None, copy=True)

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
