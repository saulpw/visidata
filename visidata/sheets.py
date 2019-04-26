from visidata import VisiData, Sheet, globalCommand, RowColorizer, ColumnAttr, ColumnItem, vd, fail, vlen, ENTER


@VisiData.global_api
def replace(vd, vs):
    'Replace top sheet with the given sheet `vs`.'
    vd.sheets.pop(0)
    return vd.push(vs)


@VisiData.global_api
def remove(vd, vs):
    if vs in vd.sheets:
        vd.sheets.remove(vs)
    else:
        fail('sheet not on stack')


@VisiData.global_api
def push(vd, vs, sheets=None):
    'Move given sheet `vs` to index 0 of list `sheets`.'
    if sheets is None:
        sheets = vd.sheets
    if vs:
        vs.vd = vd
        if vs in sheets:
            sheets.remove(vs)
        else:
            vs.creatingCommand = vd.cmdlog and vd.cmdlog.currentActiveRow

        sheets.insert(0, vs)

        if not vs.loaded:
            vs.reload()
            vs.recalc()  # set up Columns

        if vs.precious and vs not in vd.allSheets:
            vd.allSheets.append(vs)
            vs.shortcut = len(vd.allSheets)
        elif hasattr(vs, 'creatingCommand') and vs.creatingCommand:
            vs.shortcut = vs.shortcut or vs.creatingCommand.keystrokes

        return vs


@VisiData.cached_property
def sheetsSheet(vd):
    return SheetsSheet("sheets_all", source=vd.allSheets)


class SheetsSheet(Sheet):
    rowtype = 'sheets'
    precious = False
    columns = [
        ColumnAttr('name', width=30),
        ColumnAttr('shortcut'),
        ColumnAttr('nRows', type=int),
        ColumnAttr('nCols', type=int),
        ColumnAttr('nVisibleCols', type=int),
        ColumnAttr('cursorDisplay'),
        ColumnAttr('keyColNames'),
        ColumnAttr('source'),
        ColumnAttr('progressPct'),
        ColumnAttr('threads', 'currentThreads', type=vlen),
    ]
    colorizers = [
        RowColorizer(1.5, 'color_hidden_col', lambda s,c,r,v: r and r not in vd.sheets),
    ]
    nKeys = 1

    def newRow(self):
        return Sheet('', columns=[ColumnItem('', 0)], rows=[])

    def reload(self):
        self.rows = self.source


SheetsSheet.addCommand(ENTER, 'open-row', 'dest=cursorRow; vd.sheets.remove(sheet) if not sheet.precious else None; vd.push(dest)')
SheetsSheet.addCommand('g'+ENTER, 'open-rows', 'for vs in selectedRows: vd.push(vs)')
SheetsSheet.addCommand('g^R', 'reload-selected', 'for vs in selectedRows or rows: vs.reload()')
SheetsSheet.addCommand('gC', 'columns-selected', 'vd.push(ColumnsSheet("all_columns", source=selectedRows))')
SheetsSheet.addCommand('gI', 'describe-selected', 'vd.push(DescribeSheet("describe_all", source=selectedRows))')
SheetsSheet.addCommand('z^C', 'cancel-row', 'cancelThread(*cursorRow.currentThreads)')
SheetsSheet.addCommand('gz^C', 'cancel-rows', 'for vs in selectedRows: cancelThread(*vs.currentThreads)')

globalCommand('zS', 'sheets-stack', 'vd.push(SheetsSheet("sheets", source=vd.sheets))')
globalCommand('S', 'sheets-all', 'vd.push(vd.sheetsSheet)')
