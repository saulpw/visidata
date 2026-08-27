import io
import pathlib
import tarfile
import zipfile
import datetime
import os.path
from visidata.loaders import unzip_http

from visidata import vd, VisiData, asyncthread, Sheet, Progress, Menu
from visidata import ColumnAttr, Column, Path, filesize
from visidata.type_date import date

@VisiData.api
def guess_zip(vd, p):
    if not p.is_url() and zipfile.is_zipfile(p.open_bytes()):
        return dict(filetype='zip', _likelihood=10)

@VisiData.api
def guess_tar(vd, p):
    # an empty file will pass is_tarfile(), but can't be opened by tarfile.open()
    if filesize(p) == 0:
        return None
    if tarfile.is_tarfile(p.open_bytes()):
        return dict(filetype='tar', _likelihood=10)

@VisiData.api
def open_zip(vd, p):
    return vd.ZipSheet(p.base_stem, source=p)

@VisiData.api
def open_tar(vd, p):
    return TarSheet(p.base_stem, source=p)

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
        Column('filename', getter=lambda col,row: row[1].name),
        Column('abspath', type=str, width=0, getter=lambda col,row: row[1]),
        Column('ext', getter=lambda col,row: row[0].filename.endswith('/') and '/' or row[1].ext),
        Column('size', getter=lambda col,row: row[0].file_size, type=int),
        Column('compressed_size', type=int, getter=lambda col,row: row[0].compress_size),
        Column('date_time', type=date,
               getter=lambda col, row: datetime.datetime(*row[0].date_time)),
    ]
    nKeys = 2
    guide = '''# Zip Sheet
This is a list of files contained in the zipfile {sheet.displaySource}.

Once extracted, files can be loaded with `ENTER`.  A member with a
compression suffix (like `data.csv.gz`) is decompressed on the way in,
and loaded as the filetype named by the remaining extension.

Commands:

- `x` to extract current file to current directory
- `gx` to extract selected files to current directory
- `zx` to extract current file to a given pathname
- `gzx`  to extract selected files to given directory
- `open-row-filetype` to load the current file as a named filetype

'''

    def openZipFile(self, fp, *args, **kwargs):
        '''Use VisiData input to handle password-protected zip files.'''
        try:
            return fp.open(*args, **kwargs)
        except RuntimeError as err:
            if 'password required' in err.args[0]:
                pwd = vd.input(f'{args[0].filename} is encrypted, enter password: ', display=False)
                return fp.open(*args, **kwargs, pwd=pwd.encode('utf-8'))
            vd.exceptionCaught(err)

    def openRow(self, row, filetype=None):
            fi, zpath = row
            fp = self.openZipFile(self.zfp, fi)
            return vd.openSource(Path(fi.filename, fp=fp, filesize=fi.file_size), filetype=filetype)

    def extract(self, *rows, path=None):
        path = path or Path('.')

        for row in rows:
            r, _ = row
            vd.confirmOverwrite(path/r.filename)  #1452
            self.extract_async(row, path=path)

    def sysopen_row(self, row):
        'Extract file in row to tempdir and launch $EDITOR.  Modifications will be discarded.'
        with vd.TempDir() as tempdir:
            self.zfp.extract(member=row[0], path=tempdir)
            vd.launchExternalEditorPath(Path(tempdir)/row[0].filename)

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
                vd.importExternal('urllib3')
                unzip_http.warning = vd.warning
                self._zfp = unzip_http.RemoteZipFile(str(self.source))
            elif isinstance(self.source, Path):
                if self.source.has_fp():  #when opening a zip inside tar or zip
                    fp = self.source.open('rb')
                else:
                    fp = self.source
                self._zfp = zipfile.ZipFile(fp, 'r')
            else:
                self._zfp = zipfile.ZipFile(str(self.source), 'r')

        return self._zfp

    def iterload(self):
        try:
            for zi in Progress(self.zfp.infolist()):
                yield [zi, Path(zi.filename)]
        except Exception as e:
            vd.fail(f'{e}')


#from https://docs.python.org/3/library/tarfile.html#tarfile.REGTYPE
tarfile_type_names = {
    tarfile.REGTYPE:"file",
    tarfile.AREGTYPE:"file",
    tarfile.LNKTYPE:"hard link",
    tarfile.SYMTYPE:"symbolic link",
    tarfile.CHRTYPE:"character device",
    tarfile.BLKTYPE:"block device",
    tarfile.DIRTYPE:"directory",
    tarfile.FIFOTYPE:"FIFO",
    tarfile.CONTTYPE:"contiguous file",
    tarfile.GNUTYPE_LONGNAME:"GNU tar longname",
    tarfile.GNUTYPE_LONGLINK:"GNU tar longlink",
    tarfile.GNUTYPE_SPARSE:"GNU tar sparse file",
}
class TarSheet(Sheet):
    'Wrapper for `tarfile` library.'
    rowtype = 'files' # rowdef TarInfo
    guide = '''# Tar Sheet
This is a list of files contained in the tarfile {sheet.displaySource}.

Files can be loaded with `ENTER`.  A member with a compression suffix
(like `data.csv.gz`) is decompressed on the way in, and loaded as the
filetype named by the remaining extension.

Commands:

- `open-row-filetype` to load the current file as a named filetype

'''
    columns = [
        ColumnAttr('name'),
        Column('ext', getter=lambda col,row: row.isdir() and '/' or os.path.splitext(row.name)[1][1:]),
        ColumnAttr('size', type=int),
        ColumnAttr('mtime', type=date),
        Column('type', getter=lambda col, row: tarfile_type_names.get(row.type, 'unknown')),
        ColumnAttr('mode', type=int),
        ColumnAttr('uname'),
        ColumnAttr('gname')
    ]
    nKeys=1

    def openRow(self, fi, filetype=None):
            return vd.openSource(Path(fi.name, fp=self.tfp.extractfile(fi), filesize=fi.size), filetype=filetype)

    @property
    def tfp(self):
        '''Open tarfile for source.  A tar nested in another archive has no
        pathname to reopen, so it is read in place when its stream allows random
        access, and held in memory only when it cannot seek (like an archive
        piped in on stdin).'''
        if not self._tfp:
            if self.source.has_fp():
                fp = self.source.open_bytes()
                if not fp.seekable():
                    fp = io.BytesIO(fp.read())
                self._tfp = tarfile.open(fileobj=fp)
            else:
                self._tfp = tarfile.open(name=str(self.source))

        return self._tfp

    def iterload(self):
        for ti in Progress(self.tfp.getmembers()):
            yield ti


ZipSheet.init('_zfp', lambda: None, copy=True)
TarSheet.init('_tfp', lambda: None, copy=True)

ZipSheet.addCommand('x', 'extract-file', 'extract(cursorRow)', 'extract current file to current directory')
ZipSheet.addCommand('gx', 'extract-selected', 'extract(*onlySelectedRows)', 'extract selected files to current directory')
ZipSheet.addCommand('zx', 'extract-file-to', 'extract(cursorRow, path=inputPath("extract to: "))', 'extract current file to given pathname')
ZipSheet.addCommand('gzx', 'extract-selected-to', 'extract(*onlySelectedRows, path=inputPath("extract %d files to: " % nSelectedRows))', 'extract selected files to given directory')
ZipSheet.addCommand('Ctrl+O', 'sysopen-row', 'sysopen_row(cursorRow)', 'open $EDITOR with current file (modifications will be discarded)')

ZipSheet.addCommand('', 'open-row-filetype', 'vd.push(openRow(cursorRow, filetype=vd.input("open as filetype: ", type="filetype")))', 'open current file as a given filetype')
TarSheet.addCommand('', 'open-row-filetype', 'vd.push(openRow(cursorRow, filetype=vd.input("open as filetype: ", type="filetype")))', 'open current file as a given filetype')

vd.addMenuItems('''
    Row > Dive into > as filetype > open-row-filetype
''')

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
