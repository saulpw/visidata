import json

from visidata import *


def open_json(p):
    return JSONSheet(p.name, source=p, jsonlines=False)

def open_jsonl(p):
    return JSONSheet(p.name, source=p, jsonlines=True)


class JSONSheet(Sheet):
    commands = [Command(ENTER, 'pyobj-dive')]
    @async
    def reload(self):
        if not self.jsonlines:
            try:
                self.reload_json()
            except json.decoder.JSONDecodeError:
                status('trying jsonl')
                self.jsonlines = True

        if self.jsonlines:
            self.reload_jsonl()

    def reload_json(self):
        self.rows = []
        with self.source.open_text() as fp:
            r = json.load(fp, object_hook=self.addRow)
            self.rows = [r] if isinstance(r, dict) else r
            self.columns = DictKeyColumns(self.rows[0])
            self.recalc()

    def reload_jsonl(self):
        with self.source.open_text() as fp:
            self.rows = []
            for L in fp:
                self.addRow(json.loads(L))

    def addRow(self, row):
        if not self.rows:
            self.columns = DictKeyColumns(row)
            self.recalc()
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
