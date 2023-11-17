from visidata import Sheet, anytype

@Sheet.api
def hint_type_int(sheet):
    c = sheet.cursorCol
    if c.type is anytype:
        v = c.getTypedValue(sheet.cursorRow)
        if isinstance(v, int) or int(v) is not None:
            return 2, '[:onclick type-int]Set column type to integer[/] with `#`.'

@Sheet.api
def hint_type_float(sheet):
    c = sheet.cursorCol
    if c.type is anytype:
        v = c.getTypedValue(sheet.cursorRow)
        if isinstance(v, float) or float(v) is not None:
            return 1, '[:onclick type-float]Set column type to floating point[/] with `%`.'
