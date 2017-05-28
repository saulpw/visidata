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

def load_pyobj(name, pyobj, src=None):
    if isinstance(pyobj, list) or isinstance(pyobj, tuple):
        return SheetList(name, pyobj)
    elif isinstance(pyobj, dict):
        return SheetDict(name, pyobj)
    elif isinstance(pyobj, object):
        return SheetObject(name, pyobj)
    else:
        status('unknown type ' + type(pyobj))

def open_pyobj(path):
    return load_pyobj(path.name, eval(path.read_text()), path)

def getPublicAttrs(obj):
    return [k for k in dir(obj) if not k.startswith('_') and not callable(getattr(obj, k))]

def PyobjColumns(obj):
    'columns for each public attribute on an object'
    return [ColumnAttr(k, type(getattr(obj, k))) for k in getPublicAttrs(obj)]

def AttrColumns(attrnames):
    'attrnames is list of attribute names'
    return [ColumnAttr(name) for name in attrnames]


class SheetList(Sheet):
    def __init__(self, name, src, **kwargs):
        'columns is a list of strings naming attributes on the objects within the obj'
        super().__init__(name, src, **kwargs)
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
    def reload(self):
        self.columns = [ColumnItem('key', 0)]
        self.rows = list(list(x) for x in self.source.items())
        if self.rows and isinstance(self.rows[0][1], list):
            self.columns.extend(DictKeyColumns(self.rows[0]))
            self.command('e', 'if cursorColIndex > 0: source[cursorRow[0]][cursorColIndex-1] = editCell(cursorColIndex); sheet.cursorRowIndex += 1; reload()', 'edit this value')
            self.command(ENTER, 'if cursorColIndex > 0: push_pyobj(joinSheetnames(name, cursorRow[0]), cursorRow[cursorColIndex-1])', 'dive into this value')
        else:
            self.columns.append(ColumnItem('value', 1))
            self.command('e', 'source[cursorRow[0]][1] = editCell(1); sheet.cursorRowIndex += 1; reload()', 'edit this value')
            self.command(ENTER, 'push_pyobj(joinSheetnames(name, cursorRow[0]), cursorRow[1])', 'dive into this value')



def ColumnSourceAttr(name, source):
    'For using the row as attribute name on the given source Python object'
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
    import json
    return load_pyobj(p.name, json.load(p.open_text()))

# one json object per line
def open_jsonl(p):
    import json
    return load_pyobj(p.name, list(json.loads(L) for L in p.read_text().splitlines()))

