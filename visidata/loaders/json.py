import json

from visidata import vd, date, VisiData, PyobjSheet, AttrDict, stacktrace, TypedExceptionWrapper, options, visidata, ColumnItem, wrapply, TypedWrapper, Progress, Sheet, InferColumnsSheet

vd.option('json_indent', None, 'indent to use when saving json')
vd.option('json_sort_keys', False, 'sort object keys when saving to json')
vd.option('json_ensure_ascii', True, 'ensure ascii encode when saving json')
vd.option('default_colname', '', 'column name to use for non-dict rows')

@VisiData.api
def guess_json(vd, p):
    with p.open(encoding=vd.options.encoding) as fp:
        line = next(fp)

    line = line.strip()

    if line.startswith('{') and line.endswith('}'):
        return dict(filetype='jsonl')

    if line.startswith(tuple('[{')):
        return dict(filetype='json')


@VisiData.api
def open_jsonobj(vd, p):
    return JsonSheet(p.name, source=p)

@VisiData.api
def open_jsonl(vd, p):
    return JsonSheet(p.name, source=p)

VisiData.open_ndjson = VisiData.open_ldjson = VisiData.open_json = VisiData.open_jsonl


class JsonSheet(InferColumnsSheet):
    def iterload(self):
        with self.open_text_source() as fp:
            for L in fp:
                L = L.strip()
                try:
                    if not L: # skip blank lines
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
                        with self.open_text_source() as fp:
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


def _rowdict(cols, row, keep_nulls=False):
    ret = {}
    for col in cols:
        o = wrapply(col.getTypedValue, row)
        if isinstance(o, TypedExceptionWrapper):
            o = col.sheet.options.safe_error or str(o.exception)
        elif isinstance(o, TypedWrapper):
            o = o.val
        elif isinstance(o, date):
            o = col.getDisplayValue(row)
        if keep_nulls or o is not None:
            ret[col.name] = o
    return ret


@VisiData.api
def encode_json(vd, row, cols, enc=_vjsonEncoder(sort_keys=False)):
    'Return JSON string for given *row* and given *cols*.'
    return enc.encode(_rowdict(cols, row))


@VisiData.api
def save_json(vd, p, *vsheets):
    vs = vsheets[0]
    with p.open(mode='w', encoding=vs.options.save_encoding) as fp:
        try:
            indent = int(vs.options.json_indent)
        except Exception:
            indent = vs.options.json_indent

        jsonenc = _vjsonEncoder(indent=indent, sort_keys=vs.options.json_sort_keys, ensure_ascii=vs.options.json_ensure_ascii)

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
            for i, row in enumerate(vs.iterrows()):
                rowdict = _rowdict(vcols, row, keep_nulls=(i==0))
                fp.write(jsonenc.encode(rowdict) + '\n')

        if len(vs) == 0:
            vd.warning(
                "Output file is empty - cannot save headers without data for jsonl.\n"
                "Use `.jsonla` filetype to save as JSONL arrays format "
                "rather than JSONL dict format to preserve the headers."
            )


@VisiData.api
def save_jsonl(vd, p, *vsheets):
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        for vs in vsheets:
            vs.write_jsonl(fp)


@VisiData.api
def JSON(vd, s:str):
    'Parse `s` as JSON.'
    return json.loads(s)


JsonSheet.options.encoding = 'utf-8'
JsonSheet.options.regex_skip = r'^(//|#).*'

VisiData.save_ndjson = VisiData.save_jsonl
VisiData.save_ldjson = VisiData.save_jsonl

vd.addGlobals({
    'JsonSheet': JsonSheet,
    'JsonLinesSheet': JsonSheet,
})
