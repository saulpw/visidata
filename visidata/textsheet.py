import textwrap

from visidata import vd, BaseSheet, options, Sheet, ColumnItem, asyncthread
from visidata import Column, ColumnItem, vlen
from visidata import globalCommand, VisiData
import visidata


vd.option('wrap', False, 'wrap text to fit window width on TextSheet')
vd.option('save_filetype', 'tsv', 'specify default file type to save as', replay=True)


## text viewer
# rowdef: (linenum, str)
class TextSheet(Sheet):
    'Displays any iterable source, with linewrap if ``options.wrap`` is set.'
    rowtype = 'lines'  # rowdef: [linenum, text]
    filetype = 'txt'
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('text', 1),
    ]

    def iterload(self):
        yield from self.readlines(self.source)

    def readlines(self, source):
        winWidth = min(self.columns[1].width or 78, self.windowWidth-2)
        wrap = self.options.wrap
        for startingLine, text in enumerate(source):
            if wrap and text:
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth)):
                    yield [startingLine+i+1, L]
            else:
                yield [startingLine+1, text]

    def sysopen(sheet, linenum=0):
        @asyncthread
        def writelines(sheet, fn):
            with open(fn, 'w') as fp:
                for row in sheet.rows:
                    fp.write(row[1])
                    fp.write('\n')

        import tempfile
        with tempfile.NamedTemporaryFile() as temp:
            writelines(sheet, temp.name)
            vd.launchEditor(temp.name, '+%s' % linenum)
            sheet.rows = []
            for r in sheet.readlines(visidata.Path(temp.name)):
                sheet.addRow(r)


# .source is list of source text lines to 'load'
# .sourceSheet is Sheet error came from
class ErrorSheet(TextSheet):
    precious = False


class ErrorsSheet(Sheet):
    columns = [
        Column('nlines', type=vlen),
        ColumnItem('lastline', -1)
    ]
    def reload(self):
        self.rows = self.source

    def openRow(self, row):
        return ErrorSheet(source=self.cursorRow)

@VisiData.property
def allErrorsSheet(self):
    return ErrorsSheet("errors_all", source=vd.lastErrors)

@VisiData.property
def recentErrorsSheet(self):
    error = vd.lastErrors[-1] if vd.lastErrors else ''
    return ErrorSheet("errors_recent", source=error)



BaseSheet.addCommand('^E', 'error-recent', 'vd.lastErrors and vd.push(recentErrorsSheet) or status("no error")', 'view traceback for most recent error')
BaseSheet.addCommand('g^E', 'errors-all', 'vd.push(vd.allErrorsSheet)', 'view traceback for most recent errors')

Sheet.addCommand(None, 'view-cell', 'vd.push(ErrorSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), sourceSheet=sheet, source=cursorDisplay.splitlines()))', 'view contents of current cell in a new sheet'),
Sheet.addCommand('z^E', 'error-cell', 'vd.push(ErrorSheet(sheet.name+"_cell_error", sourceSheet=sheet, source=getattr(cursorCell, "error", None) or fail("no error this cell")))', 'view traceback for error in current cell')

TextSheet.addCommand('^O', 'sysopen-sheet', 'sheet.sysopen(sheet.cursorRowIndex)', 'open copy of text sheet in $EDITOR and reload on exit')


TextSheet.class_options.save_filetype = 'txt'

vd.addGlobals({'TextSheet': TextSheet, 'ErrorSheet': ErrorSheet})
