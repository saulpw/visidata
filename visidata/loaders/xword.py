import string

from visidata import *

def open_puz(p):
    return PuzSheet(p.name, source=p)

def open_xd(p):
    return CrosswordSheet(p.name, source=p)

class CrosswordsSheet(Sheet):
    rowtype = 'puzzles'
    columns = [
            Column('Author', getter=lambda col, row: row.author),
            Column('Copyright', getter=lambda col, row: row.copyright),
            Column('Notes', getter=lambda col, row: row.notes),
            Column('Postscript', getter=lambda col, row: ''.join(x for x in row.postscript if ord(x) >= ord(' '))),
            Column('Preamble', getter=lambda col, row: row.preamble),
            Column('Title', getter=lambda col, row: row.title)
            ]

    @asyncthread
    def reload(self):
        import puz

        self.rows = []

        contents = self.source.open_bytes().read()
        puzobj = puz.load(contents)
        self.addRow(puzobj)


class GridSheet(Sheet):
    rowtype = 'gridrow'  # rowdef: puzzle_row:str

    @asyncthread
    def reload(self):

        grid = self.source

        ncols = len(grid[0])
        self.columns = [ColumnItem('', i, width=2) for i in range(ncols)]

        for row in grid:
            row = list(row)
            self.addRow(row)


class CrosswordSheet(Sheet):
    rowtype = 'clues' # rowdef: (cluenum, clue, answer)

    columns = [
            Column('clue_number', getter=lambda col, row: row[0][0]+str(row[0][1])),
            Column('clue', getter=lambda col, row: row[1]),
            Column('answer', getter=lambda col, row: row[2])
            ]

    def reload(self):
        import xdfile
        self.xd = xdfile.Crossword(self.source.read_text())
        self.rows = self.xd.clues


class PuzSheet(CrosswordSheet):
    @asyncthread
    def reload(self):
        import xdfile.puz2xd
        self.xd = xdfile.puz2xd.parse_puz(self.source.read_bytes(), self.source.resolve())
        self.rows = self.xd.clues


def save_xd(p, vs):
    with p.open_text(mode='w') as fp:
        fp.write(vs.xd.to_unicode())


CrosswordsSheet.addCommand(ENTER, 'open-clues', 'vd.push(CrosswordSheet("clues_"+cursorRow.title, source=cursorRow))')
CrosswordSheet.addCommand('X', 'open-grid', 'vd.push(GridSheet("grid", source=xd.grid))')

options.set('disp_column_sep', '', GridSheet)
