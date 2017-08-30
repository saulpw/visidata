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
        cachefn = zi.filename
        if not os.path.exists(cachefn):
            with zipfile.ZipFile(self.source.resolve(), 'r') as zfp:
                zfp.extract(zi)
        return openSource(cachefn)
