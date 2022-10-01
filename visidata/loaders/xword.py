from collections import defaultdict

from visidata import VisiData, vd, Sheet, Column, asyncthread, CellColorizer, ColumnItem, ENTER


vd.option('color_xword_active', 'green', 'color of active clue')


@VisiData.api
def open_puz(vd, p):
    return PuzSheet(p.name, source=p)

@VisiData.api
def open_xd(vd, p):
    if p.is_dir():
        return CrosswordsSheet(p.name, source=p)
    return CrosswordSheet(p.name, source=p)


@VisiData.api
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
        self.rows = []
        for p in self.source.iterdir():
            self.addRow(Crossword(p.read(), str(p)))


@VisiData.api
class GridSheet(Sheet):
    rowtype = 'gridrow'  # rowdef: puzzle_row:str
    colorizers = [
        CellColorizer(7, 'color_xword_active', lambda s,c,r,v: r and s.pos in s.cells[(s.rows.index(r),c)])
    ]

    @asyncthread
    def reload(self):
        grid = self.source.xd.grid

        ncols = len(grid[0])
        self.columns = [ColumnItem('', i, width=2) for i in range(ncols)]

        for row in grid:
            row = list(row)
            self.addRow(row)

        self.cells = defaultdict(list) # [rownum, col] -> [ Apos, Dpos ] or [] (if black)

        # find starting r,c from self.pos
        for cluedir, cluenum, answer, r, c in self.source.xd.iteranswers_full():
            # across
            if cluedir == 'A':
                for i in range(0, len(answer)):
                    self.cells[(r, self.columns[c+i])].append(('A', cluenum))
            if cluedir == 'D':
                for i in range(0, len(answer)):
                    self.cells[(r+i, self.columns[c])].append(('D', cluenum))

                if cluenum == self.pos[1]:
                    self.cursorRowIndex, self.cursorVisibleColIndex = r, c


class CrosswordSheet(Sheet):
    rowtype = 'clues' # rowdef: (cluenum, clue, answer)

    columns = [
            Column('clue_number', getter=lambda col, row: row[0][0]+str(row[0][1])),
            Column('clue', getter=lambda col, row: row[1]),
            Column('answer', getter=lambda col, row: row[2])
            ]

    @asyncthread
    def reload(self):
        import xdfile
        self.xd = xdfile.xdfile(xd_contents=self.source.read_text(), filename=self.source)
        self.rows = self.xd.clues


class PuzSheet(CrosswordSheet):
    @asyncthread
    def reload(self):
        import xdfile.puz2xd
        self.xd = xdfile.puz2xd.parse_puz(self.source.read_bytes(), str(self.source))
        self.rows = self.xd.clues


@VisiData.api
def save_xd(vd, p, vs):
    with p.open_text(mode='w', encoding='utf-8') as fp:
        fp.write(vs.xd.to_unicode())


CrosswordsSheet.addCommand(ENTER, 'open-clues', 'vd.push(CrosswordSheet("clues_"+cursorRow.title, source=cursorRow))', 'open CrosswordSheet: clue answer pair for crossword')
CrosswordSheet.addCommand(ENTER, 'open-grid', 'vd.push(GridSheet("grid", source=sheet, pos=cursorRow[0]))', 'open GridSheet: grid for crossword')

GridSheet.options.disp_column_sep = ''
