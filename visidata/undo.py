# undoers
def undoAttr(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value as reference.'
    return '''lambda oldvals=[(o, getattr(o, "{attrname}")) for o in {objs}] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoAttrCopy(objs, attrname):
    'Returns a string that on eval() returns a closure that will set attrname on each obj to its former value which is copied.'
    return '''lambda oldvals=[ (o, copy(getattr(o, "{attrname}"))) for o in {objs} ] : list(setattr(o, "{attrname}", v) for o, v in oldvals)'''.format(attrname=attrname, objs=objs)

def undoSetValues(rowstr='[cursorRow]', colstr='[cursorCol]'):
    return 'lambda oldvals=[(c, r, c.getValue(r)) for c,r in itertools.product({colstr}, {rowstr})]: list(c.setValue(r, v) for c, r, v in oldvals)'.format(rowstr=rowstr, colstr=colstr)

def undoRows(sheetstr):
    return undoAttrCopy('[%s]'%sheetstr, 'rows')

undoBlocked = 'lambda: error("cannot undo")'
undoSheetRows = undoRows('sheet')
undoSheetCols = 'lambda sheet=sheet,oldcols=[copy(c) for c in columns]: setattr(sheet, "columns", oldcols)'
undoAddCols = undoAttrCopy('[sheet]', 'columns')
undoEditCell = undoSetValues('[cursorRow]', '[cursorCol]')
undoEditCells = undoSetValues('selectedRows', '[cursorCol]')
