'''slide rows/columns around'''

import visidata
from visidata import Sheet, moveListItem, vd

@Sheet.api
def slide_col(sheet, colidx, newcolidx):
    vd.addUndo(moveVisibleCol, sheet, newcolidx, colidx)
    return moveVisibleCol(sheet, colidx, newcolidx)

@Sheet.api
def slide_keycol(sheet, fromKeyColIdx, toKeyColIdx):
    vd.addUndo(moveKeyCol, sheet, toKeyColIdx, fromKeyColIdx)
    return moveKeyCol(sheet, fromKeyColIdx, toKeyColIdx)


@Sheet.api
def slide_row(sheet, rowidx, newcolidx):
    vd.addUndo(moveListItem, sheet.rows, newcolidx, rowidx)
    return moveListItem(sheet.rows, rowidx, newcolidx)


def moveKeyCol(sheet, fromKeyColIdx, toKeyColIdx):
    'Move key column to another key column position in sheet.'
    if not (1 <= toKeyColIdx <= len(sheet.keyCols)):
        vd.warning('already at edge')
        return fromKeyColIdx-1

    for col in sheet.keyCols:
        if col.keycol == fromKeyColIdx:
            col.keycol = toKeyColIdx
        elif toKeyColIdx < fromKeyColIdx:  # moving to the left
            if toKeyColIdx <= col.keycol < fromKeyColIdx:
                col.keycol += 1
        else:  # moving to the right
            if fromKeyColIdx < col.keycol <= toKeyColIdx:
                col.keycol -= 1

    # key columns are 1-indexed; columns in general are 0-indexed
    return toKeyColIdx-1


def moveVisibleCol(sheet, fromVisColIdx, toVisColIdx):
    'Move visible column to another visible index in sheet.'
    # a regular column cannot move to the left of keycols
    if 0 <= toVisColIdx < sheet.nVisibleCols:
        fromVisColIdx = min(max(fromVisColIdx, 0), sheet.nVisibleCols-1)
        fromColIdx = sheet.columns.index(sheet.visibleCols[fromVisColIdx])
        if toVisColIdx < len(sheet.keyCols):
            vd.warning('already at edge')
            return fromVisColIdx
        else:
            toColIdx = sheet.columns.index(sheet.visibleCols[toVisColIdx])
        moveListItem(sheet.columns, fromColIdx, toColIdx)
        return toVisColIdx
    else:
        vd.warning('already at edge')
        return fromVisColIdx


Sheet.addCommand('H', 'slide-left', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex-1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, cursorCol.keycol-1)', 'slide the current column left **one position**')
Sheet.addCommand('L', 'slide-right', 'sheet.cursorVisibleColIndex = slide_col(cursorVisibleColIndex, cursorVisibleColIndex+1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, cursorCol.keycol+1)', 'slide the current column right **one position**')
Sheet.addCommand('J', 'slide-down', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex+1)', 'slide current row down')
Sheet.addCommand('K', 'slide-up', 'sheet.cursorRowIndex = slide_row(cursorRowIndex, cursorRowIndex-1)', 'slide current row up')
Sheet.addCommand('gH', 'slide-leftmost', 'slide_col(cursorVisibleColIndex, len(keyCols) + 0) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, 1)', 'slide the current column **all the way** to the left of its section')
Sheet.addCommand('gL', 'slide-rightmost', 'slide_col(cursorVisibleColIndex, nVisibleCols-1) if not cursorCol.keycol else slide_keycol(cursorCol.keycol, len(keyCols))', 'slide the current column **all the way** to the right of its section')
Sheet.addCommand('gJ', 'slide-bottom', 'slide_row(cursorRowIndex, nRows)', 'slide current row all the way to the bottom of sheet')
Sheet.addCommand('gK', 'slide-top', 'slide_row(cursorRowIndex, 0)', 'slide current row to top of sheet')
Sheet.addCommand('zH', 'slide-left-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex-int(input("slide col left n=", value=1)))', 'slide current column **N positions** to the left')
Sheet.addCommand('zL', 'slide-right-n', 'slide_col(cursorVisibleColIndex, cursorVisibleColIndex+int(input("slide col left n=", value=1)))', 'slide current column **N positions** to the right')
Sheet.addCommand('zJ', 'slide-down-n', 'slide_row(cursorRowIndex, cursorRowIndex+int(input("slide row down n=", value=1)))', 'slide current row N positions down')
Sheet.addCommand('zK', 'slide-up-n', 'slide_row(cursorRowIndex, cursorRowIndex-int(input("slide row up n=", value=1)))', 'slide current row N positions up')

Sheet.bindkey('Shift+Left', 'slide-left')
Sheet.bindkey('Shift+Up', 'slide-up')
Sheet.bindkey('Shift+Down', 'slide-down')
Sheet.bindkey('Shift+Right', 'slide-right')

Sheet.bindkey('g Shift+Left', 'slide-leftmost')
Sheet.bindkey('g Shift+Down', 'slide-bottom')
Sheet.bindkey('g Shift+Up', 'slide-top')
Sheet.bindkey('g Shift+Right', 'slide-rightmost')

vd.addMenuItems('''
    Edit > Slide > Row > up > slide-up
    Edit > Slide > Row > up N > slide-up-n
    Edit > Slide > Row > down > slide-down
    Edit > Slide > Row > down N > slide-down-n
    Edit > Slide > Row > to top > slide-top
    Edit > Slide > Row > to bottom > slide-bottom
    Edit > Slide > Column > left > slide-left
    Edit > Slide > Column > left N > slide-left-n
    Edit > Slide > Column > leftmost > slide-leftmost
    Edit > Slide > Column > right > slide-right
    Edit > Slide > Column > right N > slide-right-n
    Edit > Slide > Column > rightmost > slide-rightmost
''')

## tests

sample_path = vd.pkg_resources_files(visidata) / 'tests/sample.tsv'
benchmark_path = vd.pkg_resources_files(visidata) / 'tests/benchmark.csv'

def make_tester(setup_vdx):
    def t(vdx, golden):
        global vd
        vd = visidata.vd.resetVisiData()
        vd.runvdx(setup_vdx)

        vd.runvdx(vdx)
        colnames = [c.name for c in vd.sheet.visibleCols]
        assert colnames == golden.split(), ' '.join(colnames)

    return t

def test_slide_keycol_1(vd):
    t = make_tester(f'''
            open-file {sample_path}
            +::OrderDate key-col
            +::Region key-col
            +::Rep key-col
        ''')

    t('',                             'OrderDate Region Rep Item Units Unit_Cost Total')
    t('+::Rep slide-leftmost',        'Rep OrderDate Region Item Units Unit_Cost Total')
    t('+::OrderDate slide-rightmost', 'Region Rep OrderDate Item Units Unit_Cost Total')
    t('+::Rep slide-left',            'OrderDate Rep Region Item Units Unit_Cost Total')
    t('+::OrderDate slide-right',     'Region OrderDate Rep Item Units Unit_Cost Total')

    t('''
        +::Item key-col
        +::Item slide-left
        slide-left
        slide-right
        slide-right
        slide-left
        slide-left
    ''', 'OrderDate Item Region Rep Units Unit_Cost Total')


def test_slide_leftmost(vd):
    t = make_tester(f'''open-file {benchmark_path}''')

    t('+::Paid slide-leftmost', 'Paid Date Customer SKU Item Quantity Unit')

    t = make_tester(f'''
         open-file {benchmark_path}
         +::Date key-col
    ''')

    t('', 'Date Customer SKU Item Quantity Unit Paid')
    t('''+::Item slide-leftmost''', 'Date Item Customer SKU Quantity Unit Paid')
    t('''+::SKU key-col
         +::Quantity slide-leftmost''', 'Date SKU Quantity Customer Item Unit Paid')
    t('''+::Date slide-leftmost''', 'Date Customer SKU Item Quantity Unit Paid')
    t('''+::Item slide-leftmost
         +::SKU slide-leftmost''', 'Date SKU Item Customer Quantity Unit Paid')
