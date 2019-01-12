import textwrap

from visidata.vdtui import vd, option, options, Sheet, ColumnItem, asyncthread, replayableOption

__all__ = [ 'TextSheet' ]


option('wrap', False, 'wrap text to fit window width on TextSheet')
replayableOption('save_filetype', 'tsv', 'specify default file type to save as')


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
        winWidth = min(self.columns[1].width or 78, vd.windowWidth-2)
        wrap = options.wrap
        for startingLine, text in enumerate(self.source):
            if wrap and text:
                for i, L in enumerate(textwrap.wrap(str(text), width=winWidth)):
                    self.addRow([startingLine+i+1, L])
            else:
                self.addRow([startingLine+1, text])

options.set('save_filetype', 'txt', TextSheet)

TextSheet.addCommand('v', 'visibility', 'options.set("wrap", not options.wrap, sheet); reload(); status("text%s wrapped" % ("" if options.wrap else " NOT")); ')

Sheet.addCommand('V', 'view-cell', 'vd.push(TextSheet("%s[%s].%s" % (name, cursorRowIndex, cursorCol.name), cursorDisplay.splitlines()))'),
