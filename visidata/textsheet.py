import textwrap

from visidata import vd, option, options, Sheet, ColumnItem, asyncthread
from visidata import globalCommand, error, stacktrace

__all__ = ['TextSheet', 'ErrorSheet']


option('wrap', False, 'wrap text to fit window width on TextSheet')
option('save_filetype', 'tsv', 'specify default file type to save as', replay=True)


## text viewer and dir browser
# rowdef: (linenum, str)
class TextSheet(Sheet):
    'Displays any iterable source, with linewrap if wrap set in init kwargs or options.'
    rowtype = 'lines'
    filetype = 'txt'
    columns = [
        ColumnItem('linenum', 0, type=int, width=0),
        ColumnItem('text', 1),
    ]

    def __init__(self, name, source, **kwargs):
        super().__init__(name, source=source, **kwargs)

    @asyncthread
    def reload(self):
        self.rows = []
        winWidth = min(self.columns[1].width or 78, self.windowWidth-2)
        wrap = options.wrap
        for startingLine, text in enumerate(self.source):
            if wrap and text:
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth)):
                    self.addRow([startingLine+i+1, L])
            else:
                self.addRow([startingLine+1, text])


class ErrorSheet(TextSheet):
    precious = False
    pass


globalCommand('^E', 'error-recent', 'vd.lastErrors and vd.push(ErrorSheet("last_error", vd.lastErrors[-1])) or status("no error")')
globalCommand('g^E', 'errors-all', 'vd.push(ErrorSheet("last_errors", sum(vd.lastErrors[-10:], [])))')

Sheet.addCommand('V', 'view-cell', 'vd.push(TextSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), cursorDisplay.splitlines()))'),
Sheet.addCommand('z^E', 'error-cell', 'vd.push(ErrorSheet("cell_error", getattr(cursorCell, "error", None) or fail("no error this cell")))')

TextSheet.addCommand('v', 'visibility', 'options.set("wrap", not options.wrap, sheet); reload(); status("text%s wrapped" % ("" if options.wrap else " NOT")); ')

options.set('save_filetype', 'txt', TextSheet)
