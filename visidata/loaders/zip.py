import codecs
from visidata import *

class open_zip(Sheet):
    'Provide wrapper around `zipfile` library for opening ZIP files.'
    rowtype = 'files'
    commands = [
        Command(ENTER, 'vd.push(openZipFileEntry(cursorRow))', 'open this file'),
        Command('g'+ENTER, 'for r in selectedRows or rows: vd.push(openZipFileEntry(r))', 'open all selected files')
    ]
    columns = [
        ColumnAttr('filename'),
        ColumnAttr('file_size', type=int),
        ColumnAttr('date_time'),
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
