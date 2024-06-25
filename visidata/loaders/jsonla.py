import json

from visidata import VisiData, vd, SequenceSheet, deduceType, Progress


@VisiData.api
def guess_jsonla(vd, p):
    '''A JSONLA file is a JSONL file with rows of arrays, where the first row
    is a header array:

    ["A", "B", "C"]
    [1, "blue", true]
    [2, "yellow", false]

    The header array must be a flat array of strings

    If no suitable header is found, fall back to generic JSON load.
    '''

    with p.open(encoding=vd.options.encoding) as fp:
        try:
            first_line = next(fp)
        except StopIteration:
            return

    if first_line.strip().startswith('['):
        try:
            ret = json.loads(first_line)
        except json.decoder.JSONDecodeError:
            return
        if isinstance(ret, list) and all(isinstance(v, str) for v in ret):
            return dict(filetype='jsonla')


@VisiData.api
def open_jsonla(vd, p):
    return JsonlArraySheet(p.base_stem, source=p)


class JsonlArraySheet(SequenceSheet):
    rowtype = 'rows'    # rowdef: list of Python objects decoded from JSON
    def iterload(self):
        with self.open_text_source() as fp:
            for L in fp:
                yield json.loads(L)

        # set column types from first row
        for i, c in enumerate(self.columns):
            c.type = deduceType(self.rows[0][i])


def get_jsonla_rows(sheet, cols):
    for row in Progress(sheet.rows):
        yield [vd.get_json_value(col, row) for col in cols]


class _vjsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return str(obj)


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
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        for vs in vsheets:
            write_jsonla(vs, fp)


JsonlArraySheet.options.regex_skip = r'^(//|#).*'
