import textwrap
import re

from visidata import vd, BaseSheet, options, Sheet, ColumnItem, asyncthread
from visidata import Column, vlen
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
            temp.close()  #2118
            writelines(sheet, temp.name)
            vd.launchEditor(temp.name, '+%s' % linenum)
            sheet.rows = []
            for r in sheet.readlines(visidata.Path(temp.name)):
                sheet.addRow(r)


# .source is list of source text lines to 'load'
# .sourceSheet is Sheet error came from
class ErrorSheet(TextSheet):
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('error', 1),
    ]
    guide = '''
        # Error Sheet
This is the traceback for an error.
- move cursor then {help.commands.sysopen_error}
- `q` to quit this error sheet.
    '''
    precious = False

    def sysopen_error(self, col, row):
        '''Open an external editor for the file relevant to the cursor line
        in the Error Sheet. If the cursor is on the first line, use the file
        mentioned at the end of the stack trace'''
        if self.rows and self.cursorRowIndex == 0:
            searchidx = len(self.rows) - 1
        else:
            searchidx = self.cursorRowIndex
        pat = re.compile(r'^ +File "(.*)", line (\d+), in ')
        for _, text in self.rows[searchidx::-1]: # rowdef: [linenum, text]
            match = pat.search(text)
            if match:
                vd.launchEditor(match.group(1), f'+{match.group(2)}')
                return

    def reload(self):
        src = self.source or (vd.lastErrors[-1] if vd.lastErrors else [])
        self.rows = list(enumerate(src))

class ErrorCellSheet(ErrorSheet):
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('cell_error', 1),
    ]
    guide = '''# Error Cell Sheet
This sheet shows the error that occurred when calculating a cell.
- move cursor then {help.commands.sysopen_error}
- `q` to quit this error sheet.
'''


class ErrorsSheet(Sheet):
    columns = [
        Column('nlines', type=vlen),
        ColumnItem('lastline', -1)
    ]
    def reload(self):
        self.rows = self.source or vd.lastErrors

    def openRow(self, row):
        return ErrorSheet(source=self.cursorRow)

@VisiData.lazy_property
def allErrorsSheet(self):
    return ErrorsSheet("errors_all")

@VisiData.lazy_property
def recentErrorsSheet(self):
    return ErrorSheet("errors_recent")



BaseSheet.addCommand('^E', 'error-recent', 'recentErrorsSheet.reload(); vd.push(recentErrorsSheet) if vd.lastErrors else status("no error")', 'view traceback for most recent error')
BaseSheet.addCommand('g^E', 'errors-all', 'vd.push(vd.allErrorsSheet)', 'view traceback for most recent errors')

Sheet.addCommand('z^E', 'error-cell', 'vd.push(ErrorCellSheet(sheet.name+"_cell_error", sourceSheet=sheet, source=getattr(cursorCell, "error", None) or fail("no error this cell")))', 'view traceback for error in current cell')

TextSheet.addCommand('^O', 'sysopen-sheet', 'sheet.sysopen(sheet.cursorRowIndex)', 'open copy of text sheet in $EDITOR and reload on exit')

ErrorSheet.addCommand('Enter', 'sysopen-error', 'sysopen_error(cursorCol, cursorRow)', 'open traceback line in $EDITOR')

TextSheet.options.save_filetype = 'txt'

vd.addGlobals({'TextSheet': TextSheet, 'ErrorSheet': ErrorSheet, 'ErrorCellSheet': ErrorCellSheet})

vd.addMenuItems('''
    View > Errors > recent > error-recent
    View > Errors > all > errors-all
    View > Errors > in cell > error-cell
''')
