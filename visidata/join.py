import collections
import itertools
import functools
from copy import copy

from visidata import *

@VisiData.api
def ensureLoaded(vd, sheets):
    threads = [vs.ensureLoaded() for vs in sheets]
    vd.status('loading %d sheets' % len([t for t in threads if t]))


@Sheet.api
def openJoin(sheet, others, jointype=''):
    sheets = [sheet] + others

    sheets[1:] or vd.fail("join requires more than 1 sheet")

    if jointype == 'append':
        return ConcatSheet('&'.join(vs.name for vs in sheets), source=sheets)

    for s in sheets:
        s.keyCols or vd.fail(f'{s.name} has no key cols to join')

    if jointype == 'extend':
        vs = copy(sheets[0])
        vs.name = '+'.join(vs.name for vs in sheets)
        vs.reload = functools.partial(ExtendedSheet_reload, vs, sheets)
        return vs
    else:
        return JoinSheet('+'.join(vs.name for vs in sheets), sources=sheets, jointype=jointype)


vd.jointypes = [{'key': k, 'desc': v} for k, v in {
    'inner': 'only rows which match keys on all sheets',
    'outer': 'all rows from first selected sheet',
    'full': 'all rows from all sheets (union)',
    'diff': 'only rows NOT in all sheets',
    'append': 'columns all sheets; extend with rows from all sheets',
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
                    rowsByKey[key] = [
                        dict(crow)
                          for crow in itertools.product(*[
                              [(vs2, j) for j in rowsBySheetKey[vs2].get(key, [None])]
                                  for vs2 in sheets
                          ])
                    ]


class JoinKeyColumn(Column):
    def __init__(self, name='', keycols=None, **kwargs):
        super().__init__(name, type=keycols[0].type, width=keycols[0].width, **kwargs)
        self.keycols = keycols

    def calcValue(self, row):
        vals = set()
        for i, c in enumerate(self.keycols):
            if row[c.sheet] is not None:
                vals.add(c.getDisplayValue(row[c.sheet]))
        if len(vals) == 1:
            return vals.pop()
        else:
            raise Exception(f'inconsistent keys: ' + str(vals))

    def putValue(self, row, value):
        for i, c in enumerate(self.keycols):
            if row[c.sheet] is not None:
                c.setValues([row[c.sheet]], value)

    def recalc(self, sheet=None):
        Column.recalc(self, sheet)
        for c in self.keycols:
            c.recalc()


class MergeColumn(Column):
    def calcValue(self, row):
        for vs, c in self.cols.items():
            if c:
                v = c.getTypedValue(row[vs])
                if v and not isinstance(v, TypedWrapper):
                    return v

    def putValue(self, row, value):
        for vs, c in reversed(self.cols.items()):
            c.setValue(row[vs], value)

    def isDiff(self, row, value):
        col = list(self.cols.values())[0]
        return col and value != col.getValue(row[col.sheet])

#### slicing and dicing
# rowdef: [sheet1_row, sheet2_row, ...]
#   if a sheet does not have this key, sheet#_row is None
class JoinSheet(Sheet):
    'Column-wise join/merge. `jointype` constructor arg should be one of jointypes.'
    colorizers = [
        CellColorizer(0, 'color_diff', lambda s,c,r,v: c and r and isinstance(c, MergeColumn) and c.isDiff(r, v.value))
    ]

    @asyncthread
    def reload(self):
        sheets = self.sources

        vd.ensureLoaded(sheets)
        vd.sync()

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = []

        for i, cols in enumerate(itertools.zip_longest(*(s.keyCols for s in sheets))):
            self.addColumn(JoinKeyColumn(cols[0].name, keycols=cols)) # ColumnItem(c.name, i, sheet=sheets[0], type=c.type, width=c.width)))
        self.setKeys(self.columns)

        allcols = collections.defaultdict(dict) # colname: { sheet: origcol, ... }
        for sheetnum, vs in enumerate(sheets):
            for c in vs.nonKeyVisibleCols:
                allcols[c.name][vs] = c

        if self.jointype == 'merge':
            for colname, cols in allcols.items():
                self.addColumn(MergeColumn(colname, cols=cols))
        else:
          ctr = collections.Counter(c.name for vs in sheets for c in vs.nonKeyVisibleCols)
          for sheetnum, vs in enumerate(sheets):
            # subsequent elements are the rows from each source, in order of the source sheets
            for c in vs.nonKeyVisibleCols:
                newname = c.name if ctr[c.name] == 1 else '%s_%s' % (vs.name, c.name)
                self.addColumn(SubColumnItem(vs, c, name=newname))

        rowsBySheetKey = {}   # [sheet] -> { key:list(rows), ... }
        rowsByKey = {}  # [key] -> [{sheet1:row1, sheet2:row1, ... }, ...]

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
                        if all(r is not None for r in combinedRow.values()):
                            self.addRow(combinedRow)

                elif self.jointype == 'outer':  # all rows from first sheet
                    for combinedRow in combinedRows:
                        if combinedRow[sheets[0]]:
                            self.addRow(combinedRow)

                elif self.jointype == 'diff':  # only rows without matching key on all sheets
                    for combinedRow in combinedRows:
                        if not all(r is not None for r in combinedRow.values()):
                            self.addRow(combinedRow)


## for ExtendedSheet_reload below
class ExtendedColumn(Column):
    def calcValue(self, row):
        key = joinkey(self.firstJoinSource, row)
        srcrow = self.rowsBySheetKey[self.srcsheet][key]
        if srcrow:
            return self.sourceCol.calcValue(srcrow[0])

    def putValue(self, row, value):
        key = joinkey(self.firstJoinSource, row)
        srcrow = self.rowsBySheetKey[self.srcsheet][key]
        if len(srcrow) == 1:
            self.sourceCol.putValue(srcrow[0], value)
        else:
            vd.warning('failed to modify, not able to identify unique source row')


@asyncthread
def ExtendedSheet_reload(self, sheets):
    # first item in joined row is the key tuple from the first sheet.
    # first columns are the key columns from the first sheet, using its row (0)

    vd.ensureLoaded(sheets)
    vd.sync()

    self.columns = []
    for i, c in enumerate(sheets[0].keyCols):
        self.addColumn(copy(c))
    self.setKeys(self.columns)

    for i, c in enumerate(sheets[0].nonKeyVisibleCols):
        self.addColumn(copy(c))

    self.rowsBySheetKey = {}  # [srcSheet][key] -> list(rowobjs from sheets[0])
    rowsByKey = {}  # [key] -> [{sheet1:row1, sheet2:row1, ... }, ...]

    for sheetnum, vs in enumerate(sheets[1:]):
        # subsequent elements are the rows from each source, in order of the source sheets
#        ctr = collections.Counter(c.name for c in vs.nonKeyVisibleCols)
        for c in vs.nonKeyVisibleCols:
            newname = '%s_%s' % (vs.name, c.name)
            newcol = ExtendedColumn(newname, srcsheet=vs, rowsBySheetKey=self.rowsBySheetKey, firstJoinSource=sheets[0], sourceCol=c)
            self.addColumn(newcol)

    groupRowsByKey(sheets, self.rowsBySheetKey, rowsByKey)

    self.rows = []

    with Progress(gerund='joining', total=len(rowsByKey)) as prog:
        for k, combinedRows in rowsByKey.items():
            prog.addProgress(1)
            for combinedRow in combinedRows:
                if combinedRow[sheets[0]]:
                    self.addRow(combinedRow[sheets[0]])


## for ConcatSheet
class ConcatColumn(Column):
    '''ConcatColumn(name, cols={srcsheet:srccol}, ...)'''
    def getColBySheet(self, s):
        return self.cols.get(s, None)

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
    'combination of multiple sheets by row concatenation. source=list of sheets. '
    @asyncthread
    def reload(self):
        self.columns = []
        self.addColumn(ColumnItem('origin_sheet', 0, width=0))

        # only one column with each name allowed per sheet
        keyedcols = collections.defaultdict(dict)  # name -> { sheet -> col }
        self.rows = []

        with Progress(gerund='joining', sheet=self, total=sum(vs.nRows for vs in self.source)) as prog:
            for sheet in self.source:
                if sheet.ensureLoaded():
                    vd.sync()

                for r in sheet.rows:
                    self.addRow((sheet, r))
                    prog.addProgress(1)

                for idx, col in enumerate(sheet.visibleCols):
                    if not keyedcols[col.name]:  # first column with this name/number
                        self.addColumn(ConcatColumn(col.name, cols=keyedcols[col.name], type=col.type))

                    if sheet in keyedcols[col.name]:  # two columns with same name on sheet
                        keyedcols[idx][sheet] = col  # key by column num instead
                        self.addColumn(ConcatColumn(col.name, cols=keyedcols[idx], type=col.type))
                    else:
                        keyedcols[col.name][sheet] = col



IndexSheet.addCommand('&', 'join-selected', 'left, rights = someSelectedRows[0], someSelectedRows[1:]; vd.push(left.openJoin(rights, jointype=chooseOne(jointypes)))', 'merge selected sheets with visible columns from all, keeping rows according to jointype')
IndexSheet.bindkey('g&', 'join-selected')
Sheet.addCommand('&', 'join-sheets-top2', 'vd.push(openJoin(vd.sheets[1:2], jointype=chooseOne(jointypes)))', 'concatenate top two sheets in Sheets Stack')
Sheet.addCommand('g&', 'join-sheets-all', 'vd.push(openJoin(vd.sheets[1:], jointype=chooseOne(jointypes)))', 'concatenate all sheets in Sheets Stack')

vd.addMenuItem('Data', 'Join', 'selected sheets', 'join-selected')
