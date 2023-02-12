import json

from visidata import vd, date, VisiData, PyobjSheet, AttrDict, stacktrace, TypedExceptionWrapper, options, visidata, ColumnItem, wrapply, TypedWrapper, Progress, Sheet, InferColumnsSheet, deduceType, SequenceSheet

vd.option('json_indent', None, 'indent to use when saving json')
vd.option('json_sort_keys', False, 'sort object keys when saving to json')
vd.option('default_colname', '', 'column name to use for non-dict rows')

@VisiData.api
def open_jsonobj(vd, p):
    return JsonSheet(p.name, source=p)

@VisiData.api
def open_jsonl(vd, p):
    return JsonSheet(p.name, source=p)

VisiData.open_ndjson = VisiData.open_ldjson = VisiData.open_json = VisiData.open_jsonl


def is_jsonl_header_array(L):
    ret = json.loads(L)
    return type(ret) is list and all(type(v) is str for v in ret)


@VisiData.api
def open_jsonla(vd, p):
    '''A JSONLA file is a JSONL file with rows of arrays, where the first row
    is a header array:

    ["A", "B", "C"]
    [1, "blue", true]
    [2, "yellow", false]

    The header array must be a flat array of strings

    If no suitable header is found, fall back to generic JSON load.
    '''

    with p.open_text(encoding=JsonlaSheet.options.encoding) as fp:
        first_line = next(fp)

    if is_jsonl_header_array(first_line):
        return JsonlaSheet(p.name, source=p)
    else:
        vd.warning("jsonl header array missing for %s" % p.name)
        return JsonSheet(p.name, source=p)


class JsonlaSheet(SequenceSheet):
    rowtype = 'rows'    # rowdef: list of Python objects decoded from JSON
    def iterload(self):
        with self.source.open_text(encoding=self.options.encoding) as fp:
            for L in fp:
                yield json.loads(L)

        # set column types from first row
        for i, c in enumerate(self.columns):
            c.type = deduceType(self.rows[0][i])


class JsonSheet(InferColumnsSheet):
    def iterload(self):
        with self.source.open_text(encoding=self.options.encoding) as fp:
            for L in fp:
                try:
                    if L.startswith('#'): # skip commented lines
                        continue
                    elif not L.strip(): # skip blank lines
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

        return super().addRow(row, index=index)

    def newRow(self, **fields):
        return fields

    def openRow(self, row):
        return PyobjSheet("%s[%s]" % (self.name, self.keystr(row)), source=row)

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
def encode_json(vd, row, cols, enc=_vjsonEncoder(sort_keys=False)):
    'Return JSON string for given *row* and given *cols*.'
    return enc.encode(_rowdict(cols, row))


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


@Sheet.api
def write_jsonl(vs, fp):
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder()
        with Progress(gerund='saving'):
            for row in vs.iterrows():
                rowdict = _rowdict(vcols, row)
                fp.write(jsonenc.encode(rowdict) + '\n')
        if len(vs) == 0:
            vd.warning("output file is empty - cannot save headers without data for jsonl")


@VisiData.api
def save_jsonl(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        for vs in vsheets:
            vs.write_jsonl(fp)


def get_jsonla_rows(sheet, cols):
    for row in Progress(sheet.rows):
        yield [col.getTypedValue(row) for col in cols]


@Sheet.api
def write_jsonla(vs, fp):
        vcols = vs.visibleCols
        jsonenc = _vjsonEncoder()
        with Progress(gerund='saving'):
            header = [col.name for col in vcols]
            fp.write(jsonenc.encode(header) + '\n')
            rows = get_jsonla_rows(vs, vcols)
            for row in rows:
                fp.write(jsonenc.encode(row) + '\n')


@VisiData.api
def save_jsonla(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        for vs in vsheets:
            vs.write_jsonla(fp)


JsonSheet.options.encoding = 'utf-8'
VisiData.save_ndjson = VisiData.save_jsonl
VisiData.save_ldjson = VisiData.save_jsonl

vd.addGlobals({
    'JsonSheet': JsonSheet,
    'JsonLinesSheet': JsonSheet,
})
