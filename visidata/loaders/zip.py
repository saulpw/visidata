import codecs
from visidata import *

class open_zip(Sheet):
    'Provide wrapper around `zipfile` library for opening ZIP files.'
    rowtype = 'files'
    columns = [
        ColumnAttr('filename'),
        ColumnAttr('file_size', type=int),
        Column('date_time', type=date, getter=lambda col,row: datetime.datetime(*row.date_time)),
        ColumnAttr('compress_size', type=int)
    ]

    def __init__(self, p):
        super().__init__(p.name, source=p)

    def reload(self):
        import zipfile
        with zipfile.ZipFile(self.source.resolve(), 'r') as zfp:
            self.rows = zfp.infolist()

    def openZipFileEntry(self, zi):
        import zipfile
        zfp = zipfile.ZipFile(self.source.resolve(), 'r')
        decodedfp = codecs.iterdecode(zfp.open(zi), encoding=options.encoding, errors=options.encoding_errors)
        return openSource(PathFd(zi.filename, decodedfp, filesize=zi.file_size))


open_zip.addCommand(ENTER, 'dive-row', 'vd.push(openZipFileEntry(cursorRow))')
open_zip.addCommand('g'+ENTER, 'dive-selected', 'for r in selectedRows or rows: vd.push(openZipFileEntry(r))')
