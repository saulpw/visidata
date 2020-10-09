import json
from collections import OrderedDict

from visidata import *


option('json_indent', None, 'indent to use when saving json')
option('json_sort_keys', False, 'sort object keys when saving to json')
option('default_colname', '', 'column name to use for non-dict rows')


def open_json(p):
    return JsonSheet(p.name, source=p)

def open_jsonl(p):
    return JsonLinesSheet(p.name, source=p)

open_ndjson = open_ldjson = open_jsonl


class JsonSheet(PythonSheet):
    def iterload(self):
        self.colnames = {}  # [colname] -> Column
        self.columns = []

        try:
            with self.source.open_text() as fp:
                ret = json.load(fp, object_pairs_hook=OrderedDict)

            if isinstance(ret, list):
                yield from Progress(ret)
            else:
                yield ret

        except ValueError as e:
            vd.status('trying jsonl')
            yield from JsonLinesSheet.iterload(self)

    def addRow(self, row, index=None):
        # Wrap non-dict rows in a dummy object with a predictable key name.
        # This allows for more consistent handling of rows containing scalars
        # or lists.
        if not isinstance(row, dict):
            v = {options.default_colname: row}
            row = visidata.AlwaysDict(row, **v)

        super().addRow(row, index=index)

        for k in row:
            if k not in self.colnames:
                c = ColumnItem(k, type=deduceType(row[k]))
                self.colnames[k] = c
                self.addColumn(c)
        return row

    def newRow(self):
        return {}


class JsonLinesSheet(JsonSheet):
    def iterload(self):
        self.colnames = {}  # [colname] -> Column
        self.columns = []
        with self.source.open_text() as fp:
            for L in fp:
                try:
                    yield json.loads(L, object_pairs_hook=OrderedDict)
                except Exception as e:
                    e.stacktrace = stacktrace()
                    yield TypedExceptionWrapper(json.loads, L, exception=e)


## saving json and jsonl

class Cell:
    def __init__(self, col, row):
        self.col = col
        self.row = row

    @property
    def value(cell):
        o = wrapply(cell.col.getTypedValue, cell.row)
        if isinstance(o, TypedExceptionWrapper):
            return options.safe_error or str(o.exception)
        elif isinstance(o, TypedWrapper):
            return o.val
        elif isinstance(o, date):
            return cell.col.getDisplayValue(cell.row)
        return o


class _vjsonEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super().__init__(sort_keys=options.json_sort_keys, **kwargs)
        self.safe_error = options.safe_error

    def default(self, obj):
        return obj.value if isinstance(obj, Cell) else str(obj)


def _rowdict(cols, row):
    ret = {}
    for c in cols:
        cell = Cell(c, row)
        if cell.value is not None:
            ret[c.name] = cell
    return ret


@VisiData.api
def save_json(vd, p, *vsheets):
    with p.open_text(mode='w') as fp:
        if len(vsheets) == 1:
            vs = vsheets[0]
            it = [_rowdict(vs.visibleCols, row) for row in vs.iterrows()]
        else:
            it = {vs.name: [_rowdict(vs.visibleCols, row) for row in vs.iterrows()] for vs in vsheets}

        jsonenc = _vjsonEncoder(indent=options.json_indent)
        with Progress(gerund='saving'):
            for chunk in jsonenc.iterencode(it):
                fp.write(chunk)


@VisiData.api
def save_jsonl(vd, p, *vsheets):
    with p.open_text(mode='w') as fp:
      for vs in vsheets:
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder()
        with Progress(gerund='saving'):
            for row in vs.iterrows():
                rowdict = _rowdict(vcols, row)
                fp.write(jsonenc.encode(rowdict) + '\n')


VisiData.save_ndjson = VisiData.save_jsonl
VisiData.save_ldjson = VisiData.save_jsonl
