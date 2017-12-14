import json

from visidata import *


def open_json(p):
    'Handle JSON file as a single object, via `json.load`.'
    try:
        return load_pyobj(p.name, json.load(p.open_text()))
    except json.decoder.JSONDecodeError:
        status('trying jsonl')
        return open_jsonl(p)


# one json object per line
def open_jsonl(p):
    'Handle JSON file as a list of objects, one per line, via `json.loads`.'
    return load_pyobj(p.name, list(json.loads(L) for L in p.read_text().splitlines()))


@async
def save_json(vs, fn):
    def rowdict(cols, row):
        d = {}
        for col in cols:
            try:
                d[col.name] = col.getValue(row)
            except Exception:
                pass
        return d


    with open(fn, 'w') as fp:
        vcols = vs.visibleCols
        for chunk in json.JSONEncoder().iterencode([rowdict(vcols, r) for r in Progress(vs.rows)]):
            fp.write(chunk)
