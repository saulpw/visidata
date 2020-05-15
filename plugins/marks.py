'''
Plugin for marking selected rows with a keystroke, selecting marked rows,
and viewing lists of marks and their rows.
'''

__name__ = 'marks'
__version__ = '0.1pre'
__author__ = 'Saul Pwanson <vd@saul.pw>'

from visidata import *

@VisiData.lazy_property
def marks(vd):
    return MarksSheet('marks')


class MarkSheet(TableSheet):
    pass


class MarksSheet(TableSheet):
    rowtype = "marks"  # rowdef: [mark, color, [rows]]
    columns = [
        ColumnItem('mark', 0),
        ColumnItem('color', 1),
        ColumnItem('rows', 2, type=vlen),
    ]
    colorizers = [
        RowColorizer(2, None, lambda s,c,r,v: r and r[1])
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.marknotes = list('0123456789')#lstring.ascii_digits)
        self.marks = []  #
        self.markedRows = {}  # rowid(row): [row, set(marks)]
        self.rows = []

    def getColor(self, sheet, row):
        mark = self.getMark(sheet, row)
        if not mark:
            return ''
        return self.getMarkRow(sheet, mark)[1]

    def getMark(self, sheet, row):
        mrow = self.markedRows.get(sheet.rowid(row), None)
        if not mrow:
            return ''
        if mrow[1]:
            return next(iter(mrow[1]))  # first item in set

    def getMarks(self, row):
        'Return set of all marks for given row'
        return self.markedRows[self.rowid(row)][1]

    def isMarked(self, row, mark):
        'Return True if given row has given mark'
        return mark in self.getMarks(row)

    def getMarkRow(self, sheet, mark):
        for r in self.rows:
            if r[0] == mark:
                return r
        r = [mark, 'color_note_type', MarkSheet('mark_', rows=[], columns=copy(sheet.columns))]
        self.addRow(r)
        return r

    def setMark(self, sheet, row, mark):
        rowid = self.rowid(row)
        if rowid not in self.markedRows:
            self.markedRows[rowid] = [row, set(mark)]
        else:
            self.markedRows[rowid][1].add(mark)

        vd.marks.getMarkRow(sheet, mark)[2].addRow(row)

    def unsetMark(self, sheet, row, mark):
        rowid = self.rowid(row)
        if rowid in self.markedRows:
            self.markedRows[rowid][1].remove(mark)
        vd.marks.getMarkRow(sheet, mark)[2].deleteBy(lambda r,x=row: r is x)

    def inputmark(self):
        return vd.inputsingle('mark: ') or self.marknotes.pop()

    def openRow(self, row):
        return row[2]


@VisiData.api
@asyncthread
def mark(vd, sheet, rows, m):
#    self.addUndoMark()
    for r in rows:
        vd.marks.setMark(sheet, r, m)

@VisiData.api
@asyncthread
def unmark(vd, sheet, rows, m):
#    self.addUndoMark()
    for r in rows:
        vd.marks.unsetMark(sheet, r, m)


vd.rowNoters.insert(0, lambda sheet, row: vd.marks.getMark(sheet, row))

TableSheet.colorizers.append(RowColorizer(2, None, lambda s,c,r,v: not c and r and vd.marks.getColor(s, r)))

TableSheet.addCommand('m', 'mark-row', 'vd.mark(sheet, [cursorRow], vd.marks.inputmark())', '')
TableSheet.addCommand('zm', 'unmark-row', 'vd.unmark(sheet, [cursorRow], vd.marks.inputmark())', '')
TableSheet.addCommand('gm', 'mark-selected', 'vd.mark(sheet, selectedRows, vd.marks.inputmark())', '')
TableSheet.addCommand('gzm', 'unmark-selected', 'vd.unmark(sheet, selectedRows, vd.marks.inputmark())', '')

TableSheet.addCommand('zs', 'select-marks', 'select(gatherBy(lambda r,mark=vd.marks.inputmark(): vd.marks.isMarked(r, mark)))', '')
TableSheet.addCommand('zt', 'toggle-marks', 'toggle(gatherBy(lambda r,mark=vd.marks.inputmark(): vd.marks.isMarked(r, mark)))', '')
TableSheet.addCommand('zu', 'unselect-marks', 'unselect(gatherBy(lambda r,mark=vd.marks.inputmark(): vd.marks.isMarked(r, mark)))', '')

TableSheet.addCommand('', 'open-marks', 'vd.push(vd.marks)', '')
