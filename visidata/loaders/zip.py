import codecs
from visidata import *

class open_zip(Sheet):
    'Provide wrapper around `zipfile` library for opening ZIP files.'

    commands = [
        Command(ENTER, 'vd.push(openZipFileEntry(cursorRow))', 'open this file')
    ]
    columns = AttrColumns('filename file_size date_time compress_size'.split())

    def __init__(self, p):
        super().__init__(p.name, p)

    def reload(self):
        import zipfile
        with zipfile.ZipFile(self.source.resolve(), 'r') as zfp:
            self.rows = zfp.infolist()

    def openZipFileEntry(self, zi):
        import zipfile
        zfp = zipfile.ZipFile(self.source.resolve(), 'r')
        decodedfp = codecs.iterdecode(zfp.open(zi), encoding=options.encoding, errors=options.encoding_errors)
        return openSource(PathFd(zi.filename, decodedfp, filesize=zi.file_size))
