import codecs
import tarfile
import zipfile

from visidata import *

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
    rowtype = 'files' # rowdef ZipInfo
    columns = [
        ColumnAttr('filename'),
        ColumnAttr('file_size', type=int),
        Column('date_time', type=date,
               getter=lambda col, row: datetime.datetime(*row.date_time)),
        ColumnAttr('compress_size', type=int)
    ]

    def openZipFile(self, fp, *args, **kwargs):
        '''Use VisiData input to handle password-protected zip files.'''
        try:
            return fp.open(*args, **kwargs)
        except RuntimeError as err:
            if 'password required' in err.args[0]:
                pwd = vd.input(f'{args[0].filename} is encrypted, enter password: ', display=False)
                return fp.open(*args, **kwargs, pwd=pwd.encode('utf-8'))
            vd.error(err)

    def openRow(self, fi):
            decodedfp = codecs.iterdecode(self.openZipFile(self.zfp, fi),
                                          encoding=options.encoding,
                                          errors=options.encoding_errors)
            return vd.openSource(Path(fi.filename, fp=decodedfp, filesize=fi.file_size), filetype=options.filetype)

    @asyncthread
    def extract(self, *rows, path=None):
        self.zfp.extractall(members=[r.filename for r in rows], path=path)

    @property
    def zfp(self):
        return zipfile.ZipFile(str(self.source), 'r')

    def iterload(self):
        with self.zfp as zf:
            for zi in Progress(zf.infolist()):
                yield zi


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
