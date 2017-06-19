from visidata import *

command('^O', 'expr = input("eval: ", "expr"); push_pyobj(expr, eval(expr))', 'eval Python expression and open the result')
command('^Z', 'status(type(cursorRow)); push_pyobj("%s.row[%s]" % (sheet.name, cursorRowIndex), cursorRow)', 'push sheet for this row as python object')

#### generic list/dict/object browsing
def push_pyobj(name, pyobj, src=None):
    vs = load_pyobj(name, pyobj, src)
    if vs:
        return vd().push(vs)
    else:
        status('unknown type ' + type(pyobj))

def load_pyobj(name, *args):
    """Return Sheet object of appropriate type for given sources in `args`."""
    pyobj = args[0]
    if isinstance(pyobj, list) or isinstance(pyobj, tuple):
        return SheetList(name, *args)
    elif isinstance(pyobj, dict):
        return SheetDict(name, *args)
    elif isinstance(pyobj, object):
        return SheetObject(name, *args)
    else:
        status('unknown type ' + type(pyobj))

def open_pyobj(path):
    """Provide wrapper for `load_pyobj`."""
    return load_pyobj(path.name, eval(path.read_text()), path)

def getPublicAttrs(obj):
    """Return all public attributes (not methods or `_`-prefixed) on object."""
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    """Return columns for each public attribute on an object."""
    return [ColumnAttr(k, type(getattr(obj, k))) for k in getPublicAttrs(obj)]

def AttrColumns(attrnames):
    """Return column names for all elements of list `attrnames`."""
    return [ColumnAttr(name) for name in attrnames]


class SheetList(Sheet):
    """A sheet from a list of homogenous dicts."""
    def __init__(self, name, *args, **kwargs):
        # columns is a list of strings naming attributes on the objects within the obj
        super().__init__(name, *args, **kwargs)
        src = args[0]
        assert isinstance(src, list) or isinstance(src, tuple), type(src)

    def reload(self):
        self.rows = self.source
        if self.columns:
            pass
        elif self.rows and isinstance(self.rows[0], dict):  # list of dict
            self.columns = DictKeyColumns(self.rows[0])
        else:
            self.columns = [Column(self.name)]

        self.command('^J', 'push_pyobj("%s[%s]" % (name, cursorRowIndex), cursorRow).cursorRowIndex = cursorColIndex', 'dive into this row')

class SheetDict(Sheet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command('e', 'edit()', 'edit this value')
        self.command(ENTER, 'dive()', 'dive into this value')

    def reload(self):
        self.columns = [ColumnItem('key', 0)]
        self.rows = list(list(x) for x in self.source.items())
        if self.rows and isinstance(self.rows[0][1], list):
            self.columns.extend(DictKeyColumns(self.rows[0]))
            self.dictOfList = True
        else:
            self.columns.append(ColumnItem('value', 1))
            self.dictOfList = False

    def edit(self):
        if self.dictOfList:
            if self.cursorColIndex > 0:
                self.source[self.cursorRow[0]][self.cursorColIndex-1] = self.editCell(self.cursorColIndex)
                self.cursorRowIndex += 1
                self.reload()
        else:
            self.source[self.cursorRow[0]][1] = self.editCell(1)
            self.cursorRowIndex += 1
            self.reload()

    def dive(self):
        if self.dictOfList:
            if self.cursorColIndex > 0:
                push_pyobj(joinSheetnames(self.name, self.cursorRow[0]), self.cursorRow[self.cursorColIndex-1])
        else:
            push_pyobj(joinSheetnames(self.name, self.cursorRow[0]), self.cursorRow[1])

def ColumnSourceAttr(name, source):
    """Use row as attribute name on given object `source`."""
    return Column(name, type=anytype,
        getter=lambda r,b=source: getattr(b,r),
        setter=lambda r,v,b=source: setattr(b,r,v))

class SheetObject(Sheet):
    def reload(self):
        self.rows = dir(self.source)
        self.columns = [
            Column(type(self.source).__name__ + '_attr'),
            ColumnSourceAttr('value', self.source)
        ]
        self.nKeys = 1
        self.command(ENTER, 'v = getattr(source, cursorRow); push_pyobj(joinSheetnames(name, cursorRow), v() if callable(v) else v)', 'dive into this value')
        self.command('e', 'setattr(source, cursorRow, editCell(1)); sheet.cursorRowIndex += 1; reload()', 'edit this value')


def open_json(p):
    """Handle JSON file as a single object, via `json.load`."""
    import json
    return load_pyobj(p.name, json.load(p.open_text()))

# one json object per line
def open_jsonl(p):
    """Handle JSON file as a list of objects, one per line, via `json.loads`."""
    import json
    return load_pyobj(p.name, list(json.loads(L) for L in p.read_text().splitlines()))

