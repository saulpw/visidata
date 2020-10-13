import collections
import itertools
import functools
from copy import copy

from visidata import *


def createJoinedSheet(sheets, jointype=''):
    sheets[1:] or vd.fail("join requires more than 1 sheet")

    if jointype == 'append':
        keyedcols = collections.defaultdict(list, {col.name:[col] for col in sheets[0].visibleCols})
        for s in sheets[1:]:
            for col in s.visibleCols:
                key = col.name if col.name in keyedcols else col.sheet.visibleCols.index(col)
                keyedcols[key].append(col)

        return ConcatSheet('&'.join(vs.name for vs in sheets), sourceCols=list(keyedcols.values()))

    elif jointype == 'extend':
        vs = copy(sheets[0])
        vs.name = '+'.join(vs.name for vs in sheets)
        vs.reload = functools.partial(ExtendedSheet_reload, vs, sheets)
        return vs
    else:
        return JoinSheet('+'.join(vs.name for vs in sheets), sources=sheets, jointype=jointype)

jointypes = [{'key': k, 'desc': v} for k, v in {
    'inner': 'only rows which match keys on all sheets',
    'outer': 'all rows from first selected sheet',
    'full': 'all rows from all sheets (union)',
    'diff': 'only rows NOT in all sheets',
    'append': 'only columns from first sheet; extend with rows from all sheets',
    'extend': 'only rows from first sheet; extend with columns from all sheets',
    'merge': 'merge differences from other sheets into first sheet',
}.items()]

def joinkey(sheet, row):
    return tuple(c.getDisplayValue(row) for c in sheet.keyCols)


def groupRowsByKey(sheets, rowsBySheetKey, rowsByKey):
    with Progress(gerund='grouping', total=sum(len(vs.rows) for vs in sheets)*2) as prog:
        for vs in sheets:
            # tally rows by keys for each sheet
            rowsBySheetKey[vs] = collections.defaultdict(list)
            for r in vs.rows:
                prog.addProgress(1)
                key = joinkey(vs, r)
                rowsBySheetKey[vs][key].append(r)

        for vs in sheets:
            for r in vs.rows:
                prog.addProgress(1)
                key = joinkey(vs, r)
                if key not in rowsByKey: # gather for this key has not been done yet
                    # multiplicative for non-unique keys
                    rowsByKey[key] = []
                    for crow in itertools.product(*[rowsBySheetKey[vs2].get(key, [None]) for vs2 in sheets]):
                        rowsByKey[key].append(list(crow))

class JoinKeyColumn(Column):
    def __init__(self, name='', keycols=None, **kwargs):
        super().__init__(name, type=keycols[0].type, width=keycols[0].width, **kwargs)
        self.keycols = keycols

    def calcValue(self, row):
        vals = set()
        for i, c in enumerate(self.keycols):
            if row[i] is not None:
                vals.add(c.getValue(row[i]))
        if len(vals) == 1:
            return vals.pop()
        else:
            raise Exception(f'inconsistent keys--reload join')

    def putValue(self, row, value):
        for i, c in enumerate(self.keycols):
            if row[i] is not None:
                c.setValues([row[i]], value)

    def recalc(self, sheet=None):
        Column.recalc(self, sheet)
        for c in self.keycols:
            c.recalc()


class MergeColumn(Column):
    def calcValue(self, row):
        for i, c in enumerate(self.cols):
            if c:
                v = c.getTypedValue(row[i])
                if v and not isinstance(v, TypedWrapper):
                    return v

    def putValue(self, row, value):
        for r, c in zip(row, self.cols[::-1]):
            if c:
                c.setValue(r, value)


#### slicing and dicing
# rowdef: [sheet1_row, sheet2_row, ...]
#   if a sheet does not have this key, sheet#_row is None
class JoinSheet(Sheet):
    'Column-wise join/merge. `jointype` constructor arg should be one of jointypes.'
    colorizers = [
        CellColorizer(0, 'color_diff', lambda s,c,r,v: c and r and isinstance(c, MergeColumn) and c.cols[0] and v.value != c.cols[0].getValue(r[0]))
    ]

    @asyncthread
    def reload(self):
        sheets = self.sources

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = []
        keyDict = collections.defaultdict(list)

        for s in sheets:
            for keyCol in s.keyCols:
                keyDict[keyCol.name].append(keyCol)

        for i, cols in enumerate(keyDict.values()):
            self.addColumn(JoinKeyColumn(name=cols[0].name, keycols=cols)) # ColumnItem(c.name, i, sheet=sheets[0], type=c.type, width=c.width)))
        self.setKeys(self.columns)

        allcols = collections.defaultdict(lambda n=len(sheets): [None]*n)
        for sheetnum, vs in enumerate(sheets):
            for c in vs.nonKeyVisibleCols:
                allcols[c.name][sheetnum] = c

        if self.jointype == 'merge':
            for colname, cols in allcols.items():
                self.addColumn(MergeColumn(colname, cols=cols))
        else:
          ctr = collections.Counter(c.name for vs in sheets for c in vs.nonKeyVisibleCols)
          for sheetnum, vs in enumerate(sheets):
            # subsequent elements are the rows from each source, in order of the source sheets
            for c in vs.nonKeyVisibleCols:
                newname = c.name if ctr[c.name] == 1 else '%s_%s' % (vs.name, c.name)
                self.addColumn(SubColumnItem(sheetnum, c, name=newname))

        rowsBySheetKey = {}
        rowsByKey = {}

        groupRowsByKey(sheets, rowsBySheetKey, rowsByKey)

        self.rows = []

        with Progress(gerund='joining', total=len(rowsByKey)) as prog:
            for k, combinedRows in rowsByKey.items():
                prog.addProgress(1)

                if self.jointype in ['full', 'merge']:  # keep all rows from all sheets
                    for combinedRow in combinedRows:
                        self.addRow(combinedRow)

                elif self.jointype == 'inner':  # only rows with matching key on all sheets
                    for combinedRow in combinedRows:
                        if all(combinedRow):
                            self.addRow(combinedRow)

                elif self.jointype == 'outer':  # all rows from first sheet
                    for combinedRow in combinedRows:
                        if combinedRow[0]:
                            self.addRow(combinedRow)

                elif self.jointype == 'diff':  # only rows without matching key on all sheets
                    for combinedRow in combinedRows:
                        if not all(combinedRow):
                            self.addRow(combinedRow)


## for ExtendedSheet_reload below
class ExtendedColumn(Column):
    def calcValue(self, row):
        key = joinkey(self.sheet.joinSources[0], row)
        srcsheet = self.sheet.joinSources[self.sheetnum]
        srcrow = self.sheet.rowsBySheetKey[srcsheet][key]
        if srcrow[0]:
            return self.sourceCol.calcValue(srcrow[0])


@asyncthread
def ExtendedSheet_reload(self, sheets):
    self.joinSources = sheets

    # first item in joined row is the key tuple from the first sheet.
    # first columns are the key columns from the first sheet, using its row (0)
    self.columns = []
    for i, c in enumerate(sheets[0].keyCols):
        self.addColumn(copy(c))
    self.setKeys(self.columns)

    for i, c in enumerate(sheets[0].nonKeyVisibleCols):
        self.addColumn(copy(c))

    for sheetnum, vs in enumerate(sheets[1:]):
        # subsequent elements are the rows from each source, in order of the source sheets
#        ctr = collections.Counter(c.name for c in vs.nonKeyVisibleCols)
        for c in vs.nonKeyVisibleCols:
            newname = '%s_%s' % (vs.name, c.name)
            newcol = ExtendedColumn(newname, sheetnum=sheetnum+1, sourceCol=c)
            self.addColumn(newcol)

    self.rowsBySheetKey = {}  # [srcSheet][key] -> list(rowobjs from sheets[0])
    rowsByKey = {}  # [key] -> [rows0, rows1, ...]

    groupRowsByKey(sheets, self.rowsBySheetKey, rowsByKey)

    self.rows = []

    with Progress(gerund='joining', total=len(rowsByKey)) as prog:
        for k, combinedRows in rowsByKey.items():
            prog.addProgress(1)
            for combinedRow in combinedRows:
                if combinedRow[0]:
                    self.addRow(combinedRow[0])


## for ConcatSheet
class ConcatColumn(Column):
    def __init__(self, name, cols, **kwargs):
        super().__init__(name, **kwargs)
        self.cols = cols

    def getColBySheet(self, s):
        for c in self.cols:
            if c.sheet is s:
                return c

    def calcValue(self, row):
        srcSheet, srcRow = row
        srcCol = self.getColBySheet(srcSheet)
        if srcCol:
            return srcCol.calcValue(srcRow)

    def setValue(self, row, v):
        srcSheet, srcRow = row
        srcCol = self.getColBySheet(srcSheet)
        if srcCol:
            srcCol.setValue(srcRow, v)
        else:
            vd.fail('column not on source sheet')


# rowdef: (srcSheet, srcRow)
class ConcatSheet(Sheet):
    'combination of multiple sheets by row concatenation. sourceCols=list(cols). '
    @asyncthread
    def reload(self):
        self.rows = []
        sourceSheets = []
        for cols in self.sourceCols:
            for c in cols:
                if c.sheet not in sourceSheets:
                    sourceSheets.append(c.sheet)

        self.columns = []
        self.addColumn(ColumnItem('origin_sheet', 0, width=0))
        for cols in self.sourceCols:
            self.addColumn(ConcatColumn(cols[0].name, cols, type=cols[0].type))

        for sheet in sourceSheets:
            for r in Progress(sheet.rows):
                self.addRow((sheet, r))


IndexSheet.addCommand('&', 'join-sheets', 'vd.push(createJoinedSheet(selectedRows or fail("no sheets selected to join"), jointype=chooseOne(jointypes)))', 'merge selected sheets with visible columns from all, keeping rows according to jointype')
Sheet.addCommand('&', 'join-sheets-top2', 'vd.push(createJoinedSheet(vd.sheets[:2], jointype=chooseOne(jointypes)))', 'concatenate top two sheets in Sheets Stack')
Sheet.addCommand('g&', 'join-sheets-all', 'vd.push(createJoinedSheet(vd.sheets, jointype=chooseOne(jointypes)))', 'concatenate all sheets in Sheets Stack')
