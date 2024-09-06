import collections
import itertools
import functools
from copy import copy

from visidata import vd, VisiData, asyncthread, Sheet, Progress, IndexSheet, Column, CellColorizer, ColumnItem, SubColumnItem, TypedWrapper, ColumnsSheet, AttrDict

vd.help_join = '# Join Help\nHELPTODO'

@VisiData.api
def ensureLoaded(vd, sheets):
    threads = [vs.ensureLoaded() for vs in sheets]
    threads = [t for t in threads if t]
    if threads:
        vd.status('loading %d source sheets' % len(threads))
    return threads


@asyncthread
def _appendRowsAfterLoading(joinsheet, origsheets):
    with Progress(gerund='loading'):
        vd.ensureLoaded(origsheets)
        vd.sync()

    colnames = {c.name:c for c in joinsheet.visibleCols}
    for vs in origsheets:
        joinsheet.rows.extend(vs.rows)
        for c in vs.visibleCols:
            if c.name not in colnames:
                newcol = copy(c)
                colnames[c.name] = newcol
                joinsheet.addColumn(newcol)


@VisiData.api
def join_sheets_cols(vd, cols, jointype:str=''):
    'match joinkeys by cols in order per sheet.'
    sheetkeys = collections.defaultdict(list)  # [sheet] -> list of keycols on that sheet
    for c in cols:
        sheetkeys[c.sheet].append(c)

    sheets = list(sheetkeys.keys())
    return JoinSheet('+'.join(vs.name for vs in sheets),
                     sources=sheets,
                     sheetKeyCols=sheetkeys,
                     jointype=jointype)


@Sheet.api
def openJoin(sheet, others, jointype=''):
    sheets = [sheet] + others

    sheets[1:] or vd.fail("join requires more than 1 sheet")

    if jointype == 'concat':
        name = '&'.join(vs.name for vs in sheets)
        sheettypes = set(type(vs) for vs in sheets)
        if len(sheettypes) != 1:  # only one type of sheet #1598
            vd.fail(f'only same sheet types can be concat-joined; use "append"')

        joinsheet = copy(sheet)
        joinsheet.name = name
        joinsheet.rows = []
        joinsheet.source = sheets

        _appendRowsAfterLoading(joinsheet, sheets)

        return joinsheet

    elif jointype == 'append':
        name = '&'.join(vs.name for vs in sheets)
        return ConcatSheet(name, source=sheets)

    nkeys = set(len(s.keyCols) for s in sheets)
    if 0 in nkeys or len(nkeys) != 1:
        vd.fail(f'all sheets must have the same number of key columns')

    if jointype == 'extend':
        vs = copy(sheets[0])
        vs.name = '+'.join(vs.name for vs in sheets)
        vs.sheetKeyCols = {vs:vs.keyCols for vs in sheets}
        vs.reload = functools.partial(ExtendedSheet_reload, vs, sheets)
        return vs
    else:
        return JoinSheet('+'.join(vs.name for vs in sheets),
                         sources=sheets,
                         jointype=jointype,
                         sheetKeyCols={s:s.keyCols for s in sheets})


vd.jointypes = [AttrDict(key=k, desc=v) for k, v in {
    'inner': 'only rows with matching keys on all sheets',
    'outer': 'only rows with matching keys on first selected sheet',
    'full': 'all rows from all sheets (union)',
    'diff': 'only rows NOT in all sheets',
    'append': 'all rows from all sheets; columns from all sheets',
    'concat': 'all rows from all sheets; columns and type from first sheet',
    'extend': 'only rows from first sheet; type from first sheet; columns from all sheets',
    'merge': 'all rows from all sheets; where keys match, use latest truthy value',
}.items()]

def joinkey(sheetKeyCols, row):
    return tuple(c.getDisplayValue(row) for c in sheetKeyCols)


def groupRowsByKey(sheets:dict, rowsBySheetKey, rowsByKey):
    with Progress(gerund='grouping', total=sum(len(vs.rows) for vs in sheets)*2) as prog:
        for vs in sheets:
            # tally rows by keys for each sheet
            rowsBySheetKey[vs] = collections.defaultdict(list)
            for r in vs.rows:
                prog.addProgress(1)
                key = joinkey(sheets[vs], r)
                rowsBySheetKey[vs][key].append(r)

        for vs in sheets:
            for r in vs.rows:
                prog.addProgress(1)
                key = joinkey(sheets[vs], r)
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
                vals.add(c.getTypedValue(row[c.sheet]))
        if len(vals) != 1:
            keycolnames = ', '.join([f'{col.sheet.name}:{col.name}' for col in self.keycols])
            vd.warning(f"source key columns ({keycolnames}) have different types")
        return vals.pop()

    def putValue(self, row, value):
        for i, c in enumerate(self.keycols):
            if row[c.sheet] is not None:
                c.setValues([row[c.sheet]], value)

    def recalc(self, sheet=None):
        Column.recalc(self, sheet)
        for c in self.keycols:
            c.recalc()


class MergeColumn(Column):
    # .cols is { sheet: col, ... } in sheet-join order
    def calcValue(self, row):
        'Return value from last joined sheet with truth-y value in this column for the given row.'
        for vs, c in reversed(list(self.cols.items())):
            if c:
                v = c.getTypedValue(row[vs])
                if v and not isinstance(v, TypedWrapper):
                    return v

    def putValue(self, row, value):
        for vs, c in reversed(list(self.cols.items())):
            c.setValue(row[vs], value)

    def isDiff(self, row, value):
        col = list(self.cols.values())[0]
        if not col:
            return False
        if row[col.sheet] is None:
            return True
        return value != col.getValue(row[col.sheet])


#### slicing and dicing
# rowdef: {sheet1:sheet1_row, sheet2:sheet2_row, ...}
#   if a sheet does not have this key, sheet#_row is None
class JoinSheet(Sheet):
    'Column-wise join/merge. `jointype` constructor arg should be one of jointypes.'
    colorizers = [
        CellColorizer(0, 'color_diff', lambda s,c,r,v: c and r and isinstance(c, MergeColumn) and c.isDiff(r, v.value))
    ]

    sheetKeyCols = {}  # [sheet] -> list of joinkeycols for that sheet

    def loader(self):
        sheets = self.sources

        with Progress(gerund='loading'):
            vd.ensureLoaded(sheets)
            vd.sync()

        # first item in joined row is the key tuple from the first sheet.
        # first columns are the key columns from the first sheet, using its row (0)
        self.columns = []

        for i, cols in enumerate(itertools.zip_longest(*list(self.sheetKeyCols.values()))):
            self.addColumn(JoinKeyColumn(cols[0].name, keycols=cols)) # ColumnItem(c.name, i, sheet=sheets[0], type=c.type, width=c.width)))
        self.setKeys(self.columns)

        allcols = collections.defaultdict(dict) # colname: { sheet: origcol, ... }
        # MergeColumn relies on allcols having sheets in this specific order
        for sheetnum, vs in enumerate(sheets):
            for c in vs.visibleCols:
                if c not in self.sheetKeyCols[vs]:
                    allcols[c.name][vs] = c

        if self.jointype == 'merge':
            for colname, cols in allcols.items():
                self.addColumn(MergeColumn(colname, cols=cols))
        else:
          ctr = collections.Counter(c.name for vs in sheets for c in vs.visibleCols if c not in self.sheetKeyCols[vs])
          for sheetnum, vs in enumerate(sheets):
              # subsequent elements are the rows from each source, in order of the source sheets
              for c in vs.visibleCols:
                  if c not in self.sheetKeyCols[vs]:
                      newname = c.name if ctr[c.name] == 1 else '%s_%s' % (vs.name, c.name)
                      self.addColumn(SubColumnItem(vs, c, name=newname))

        rowsBySheetKey = {}   # [sheet] -> { key:list(rows), ... }
        rowsByKey = {}  # [key] -> [{sheet1:row1, sheet2:row1, ... }, ...]

        groupRowsByKey(self.sheetKeyCols, rowsBySheetKey, rowsByKey)

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
        key = joinkey(self.firstJoinSource.keyCols, row)
        srcrow = self.rowsBySheetKey[self.srcsheet][key]
        if srcrow:
            return self.sourceCol.calcValue(srcrow[0])

    def putValue(self, row, value):
        key = joinkey(self.firstJoinSource.keyCols, row)
        srcrow = self.rowsBySheetKey[self.srcsheet][key]
        if len(srcrow) == 1:
            self.sourceCol.putValue(srcrow[0], value)
        else:
            vd.warning('failed to modify, not able to identify unique source row')


@asyncthread
def ExtendedSheet_reload(self, sheets):
    # first item in joined row is the key tuple from the first sheet.
    # first columns are the key columns from the first sheet, using its row (0)

    with Progress(gerund='loading'):
        vd.ensureLoaded(sheets)
        vd.sync()

    self.columns = []
    for i, c in enumerate(sheets[0].keyCols):
        self.addColumn(copy(c))
    self.setKeys(self.columns)

    for i, c in enumerate(sheets[0].visibleCols):
        if c not in self.sheetKeyCols[c.sheet]:
            self.addColumn(copy(c))

    self.rowsBySheetKey = {}  # [srcSheet][key] -> list(rowobjs from sheets[0])
    rowsByKey = {}  # [key] -> [{sheet1:row1, sheet2:row1, ... }, ...]

    for sheetnum, vs in enumerate(sheets[1:]):
        # subsequent elements are the rows from each source, in order of the source sheets
#        ctr = collections.Counter(c.name for c in vs.visibleCols if c not in sheetkeys[vs])
        for c in vs.visibleCols:
            if c not in self.sheetKeyCols[c.sheet]:
                newname = '%s_%s' % (vs.name, c.name)
                newcol = ExtendedColumn(newname, srcsheet=vs, rowsBySheetKey=self.rowsBySheetKey, firstJoinSource=sheets[0], sourceCol=c)
                self.addColumn(newcol)

    groupRowsByKey(self.sheetKeyCols, self.rowsBySheetKey, rowsByKey)

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
    columns = [ColumnItem('origin_sheet', 0, width=0)]
    def iterload(self):
        # only one column with each name allowed per sheet
        keyedcols = collections.defaultdict(dict)  # name -> { sheet -> col }

        with Progress(gerund='loading'):
            vd.ensureLoaded(self.source)
            vd.sync()
        with Progress(gerund='joining', sheet=self, total=sum(vs.nRows for vs in self.source)) as prog:
            for sheet in self.source:
                for r in sheet.rows:
                    yield (sheet, r)
                    prog.addProgress(1)

                for idx, col in enumerate(sheet.visibleCols):
                    if not keyedcols[col.name]:  # first column with this name/number
                        self.addColumn(ConcatColumn(col.name, cols=keyedcols[col.name], type=col.type))

                    if sheet in keyedcols[col.name]:  # two columns with same name on sheet
                        keyedcols[idx][sheet] = col  # key by column num instead
                        self.addColumn(ConcatColumn(col.name, cols=keyedcols[idx], type=col.type))
                    else:
                        keyedcols[col.name][sheet] = col


@VisiData.api
def chooseJointype(vd):
    prompt = 'choose jointype: '
    def _fmt_aggr_summary(match, row, trigger_key):
        formatted_jointype = match.formatted.get('key', row.key) if match else row.key
        r = ' '*(len(prompt)-3)
        r += f'[:keystrokes]{trigger_key}[/]  '
        r += formatted_jointype
        if row.desc:
            r += ' - '
            r += match.formatted.get('desc', row.desc) if match else row.desc
        return r

    return vd.activeSheet.inputPalette(prompt,
            vd.jointypes,
            value_key='key',
            formatter=_fmt_aggr_summary,
            help=vd.help_join,
            type='jointype')


IndexSheet.addCommand('&', 'join-selected', 'left, rights = someSelectedRows[0], someSelectedRows[1:]; vd.push(left.openJoin(rights, jointype=chooseJointype()))', 'merge selected sheets with visible columns from all, keeping rows according to jointype')
IndexSheet.bindkey('g&', 'join-selected')
Sheet.addCommand('&', 'join-sheets-top2', 'vd.push(openJoin(vd.sheets[1:2], jointype=chooseJointype()))', 'concatenate top two sheets in Sheets Stack')
Sheet.addCommand('g&', 'join-sheets-all', 'vd.push(openJoin(vd.sheets[1:], jointype=chooseJointype()))', 'concatenate all sheets in Sheets Stack')

ColumnsSheet.addCommand('&', 'join-sheets-cols', 'vd.push(join_sheets_cols(selectedRows, jointype=chooseJointype()))', '')

vd.addMenuItems('''
    Data > Join > selected sheets > join-selected
    Data > Join > top two sheets > join-sheets-top2
    Data > Join > all sheets > join-sheets-all
''')

IndexSheet.guide += '''
    - `&` to join the selected sheets together
'''
