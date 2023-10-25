from visidata import vd, Column, Sheet, asyncthread, Progress


class HistogramColumn(Column):
    def calcValue(col, row):
        histogram = col.sheet.options.disp_histogram
        histolen = (col.width-2)*col.sourceCol.getTypedValue(row)//(col.sourceCol.largest-col.sourceCol.smallest)
        return histogram*histolen


@Sheet.api
def addcol_histogram(sheet, col):  #2052
    newcol = HistogramColumn(col.name+'_histogram', sourceCol=col)
    col.smallest = None
    col.largest = None
    sheet.calc_histogram_bounds(col)
    return newcol


@Sheet.api
@asyncthread
def calc_histogram_bounds(sheet, col):
    for row in Progress(sheet.rows):
        v = col.getTypedValue(row)
        if col.smallest is None or v < col.smallest:
            col.smallest = v
        if col.largest is None or v > col.largest:
            col.largest = v


Sheet.addCommand('', 'addcol-histogram', 'addColumnAtCursor(addcol_histogram(cursorCol))', 'add column with histogram of current column')


vd.addMenuItems('Column > Add column > histogram > addcol-histogram')
