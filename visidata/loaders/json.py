import json

from visidata import *


def open_json(p):
    return JSONSheet(p.name, source=p)

def open_jsonl(p):
    return JSONSheet(p.name, source=p)


class JSONSheet(Sheet):
    @async
    def reload(self):
        self.rows = []
        try:
            with self.source.open_text() as fp:
                self.rows = json.load(fp, object_hook=self.addRow)
                self.columns = DictKeyColumns(self.rows[0])
        except json.decoder.JSONDecodeError:
            with self.source.open_text() as fp:
                self.rows = []
                for L in fp:
                    self.addRow(json.loads(L))

    def addRow(self, row):
        if not self.rows:
            self.columns = DictKeyColumns(row)
        self.rows.append(row)
        return row

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
