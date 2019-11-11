import json

from visidata import vd, options, option, status, date, deduceType
from visidata import Sheet, PythonSheet, ColumnItem, stacktrace, asyncthread, Progress
from visidata import wrapply, TypedExceptionWrapper, TypedWrapper


option('json_indent', None, 'indent to use when saving json')
option('json_sort_keys', True, 'sort object keys when saving to json')


class JsonSheet(PythonSheet):
    def iterload(self):
        self.colnames = {}  # [colname] -> Column
        self.columns = []

        try:
            with self.source.open_text() as fp:
                ret = json.load(fp)

            if isinstance(ret, dict):
                yield ret
                for k in ret:
                    self.addColumn(ColumnItem(k, type=deduceType(self.rows[0][k])))
            else:
                yield from Progress(ret)

        except ValueError as e:
            status('trying jsonl')
            yield from JsonLinesSheet.iterload(self)

    def addRow(self, row, index=None):
        super().addRow(row, index=index)
        if isinstance(row, dict):
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
                    yield json.loads(L)
                except Exception as e:
                    e.stacktrace = stacktrace()
                    yield TypedExceptionWrapper(json.loads, L, exception=e)


## saving json and jsonl

class Cell:
    def __init__(self, col, row):
        self.col = col
        self.row = row

class _vjsonEncoder(json.JSONEncoder):
    def __init__(self, **kwargs):
        super().__init__(sort_keys=options.json_sort_keys, **kwargs)
        self.safe_error = options.safe_error

    def default(self, cell):
        o = wrapply(cell.col.getTypedValue, cell.row)
        if isinstance(o, TypedExceptionWrapper):
            return self.safe_error or str(o.exception)
        elif isinstance(o, TypedWrapper):
            return o.val
        elif isinstance(o, date):
            return cell.col.getDisplayValue(cell.row)
        return o


def _rowdict(cols, row):
    return {c.name: Cell(c, row) for c in cols}


@Sheet.api
def save_json(vs, p):
    with p.open_text(mode='w') as fp:
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder(indent=options.json_indent)
        for chunk in jsonenc.iterencode([_rowdict(vcols, r) for r in Progress(vs.rows, 'saving')]):
            fp.write(chunk)


@Sheet.api
def save_jsonl(vs, p):
    with p.open_text(mode='w') as fp:
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder()
        for r in Progress(vs.rows, 'saving'):
            rowdict = _rowdict(vcols, r)
            fp.write(jsonenc.encode(rowdict) + '\n')

Sheet.save_ndjson = Sheet.save_jsonl
Sheet.save_ldjson = Sheet.save_jsonl

vd.filetype('json', JsonSheet)
vd.filetype('jsonl', JsonLinesSheet)
vd.filetype('ndjson', JsonLinesSheet)
vd.filetype('ldjson', JsonLinesSheet)
