import json
from collections import OrderedDict

from visidata import *


option('json_indent', None, 'indent to use when saving json')
option('json_sort_keys', False, 'sort object keys when saving to json')
option('default_colname', '', 'column name to use for non-dict rows')


def open_jsonobj(p):
    return JsonSheet(p.name, source=p)

def open_jsonl(p):
    return JsonSheet(p.name, source=p)

open_ndjson = open_ldjson = open_json = open_jsonl


class JsonSheet(PythonSheet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._colnames = {}  # [colname] -> Column

    def addColumn(self, *cols, index=None):
        super().addColumn(*cols, index=index)
        self._colnames.update({col.name: col for col in cols })
        return cols[0]

    def iterload(self):
        self.columns = []
        self._colnames.clear()
        for c in type(self).columns:
            self.addColumn(deepcopy(c))

        with self.source.open_text(encoding=self.options.encoding) as fp:
            for L in fp:
                try:
                    if L.startswith('#'): # skip commented lines
                        continue
                    ret = json.loads(L, object_hook=AttrDict)
                    if isinstance(ret, list):
                        yield from ret
                    else:
                        yield ret

                except ValueError as e:
                    if self.rows:   # if any rows have been added already
                        e.stacktrace = stacktrace()
                        yield TypedExceptionWrapper(json.loads, L, exception=e)  # an error on one line
                    else:
                        with self.source.open_text(encoding=self.options.encoding) as fp:
                            ret = json.load(fp)
                            if isinstance(ret, list):
                                yield from ret
                            else:
                                yield ret
                        break


    def addRow(self, row, index=None):
        # Wrap non-dict rows in a dummy object with a predictable key name.
        # This allows for more consistent handling of rows containing scalars
        # or lists.
        if not isinstance(row, dict):
            v = {options.default_colname: row}
            row = visidata.AlwaysDict(row, **v)

        super().addRow(row, index=index)

        for k in row:
            k = maybe_clean(k, self)
            if k not in self._colnames:
                self.addColumn(ColumnItem(k, type=deduceType(row[k])))
        return row

    def newRow(self):
        return {}

JsonLinesSheet=JsonSheet

## saving json and jsonl

class _vjsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


def _rowdict(cols, row):
    ret = {}
    for col in cols:
        o = wrapply(col.getTypedValue, row)
        if isinstance(o, TypedExceptionWrapper):
            o = col.sheet.options.safe_error or str(o.exception)
        elif isinstance(o, TypedWrapper):
            o = o.val
        elif isinstance(o, date):
            o = col.getDisplayValue(row)
        if o is not None:
            ret[col.name] = o
    return ret


@VisiData.api
def save_json(vd, p, *vsheets):
    vs = vsheets[0]
    with p.open_text(mode='w', encoding=vs.options.encoding) as fp:
        try:
            indent = int(vs.options.json_indent)
        except Exception:
            indent = vs.options.json_indent

        jsonenc = _vjsonEncoder(indent=indent, sort_keys=vs.options.json_sort_keys)

        if len(vsheets) == 1:
            fp.write('[\n')
            vs = vsheets[0]
            with Progress(gerund='saving'):
                for i, row in enumerate(vs.iterrows()):
                    if i > 0:
                        fp.write(',\n')
                    rd = _rowdict(vs.visibleCols, row)
                    fp.write(jsonenc.encode(rd))
            fp.write('\n]\n')
        else:
            it = {vs.name: [_rowdict(vs.visibleCols, row) for row in vs.iterrows()] for vs in vsheets}

            with Progress(gerund='saving'):
                for chunk in jsonenc.iterencode(it):
                    fp.write(chunk)


@VisiData.api
def save_jsonl(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
      for vs in vsheets:
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder()
        with Progress(gerund='saving'):
            for row in vs.iterrows():
                rowdict = _rowdict(vcols, row)
                fp.write(jsonenc.encode(rowdict) + '\n')


JsonSheet.class_options.encoding = 'utf-8'
VisiData.save_ndjson = VisiData.save_jsonl
VisiData.save_ldjson = VisiData.save_jsonl
