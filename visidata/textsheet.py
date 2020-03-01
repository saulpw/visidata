import textwrap

from visidata import vd, option, options, Sheet, ColumnItem, asyncthread
from visidata import globalCommand, error, stacktrace, VisiData

__all__ = ['TextSheet', 'ErrorSheet']


option('wrap', False, 'wrap text to fit window width on TextSheet')
option('save_filetype', 'tsv', 'specify default file type to save as', replay=True)


## text viewer
# rowdef: (linenum, str)
class TextSheet(Sheet):
    'Displays any iterable source, with linewrap if wrap set in init kwargs or options.'
    rowtype = 'lines'
    filetype = 'txt'
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('text', 1),
    ]

    def iterload(self):
        winWidth = min(self.columns[1].width or 78, self.windowWidth-2)
        wrap = options.wrap
        for startingLine, text in enumerate(self.source):
            if wrap and text:
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth)):
                    yield [startingLine+i+1, L]
            else:
                yield [startingLine+1, text]


# .source is Sheet error came from
# .lines is list of source text lines to 'load'
class ErrorSheet(TextSheet):
    precious = False
    def iterload(self):
        'Uses .lines; .source is sheet causing the error.'
        for i, line in enumerate(self.lines):
            yield [i, line]

@VisiData.property
def allErrorsSheet(self):
    return ErrorSheet("errors_all", lines=sum(vd.lastErrors, []))

@VisiData.property
def recentErrorsSheet(self):
    return ErrorSheet("errors_recent", lines=sum(vd.lastErrors[-1:], []))


globalCommand('^E', 'error-recent', 'vd.lastErrors and vd.push(recentErrorsSheet) or status("no error")', 'view traceback for most recent error')
globalCommand('g^E', 'errors-all', 'vd.push(vd.allErrorsSheet)', 'view traceback for most recent errors')

Sheet.addCommand(None, 'view-cell', 'vd.push(ErrorSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), source=sheet, lines=cursorDisplay.splitlines()))', 'view contents of current cell in a new sheet'),
Sheet.addCommand('z^E', 'error-cell', 'vd.push(ErrorSheet(sheet.name+"_cell_error", source=sheet, lines=getattr(cursorCell, "error", None) or fail("no error this cell")))', 'view traceback for error in current cell')

TextSheet.addCommand('v', 'visibility', 'options.set("wrap", not options.wrap, sheet); reload(); status("text%s wrapped" % ("" if options.wrap else " NOT")); ')

options.set('save_filetype', 'txt', TextSheet)
