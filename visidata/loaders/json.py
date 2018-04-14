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
        self.colnames = {}  # [colname] -> Column
        self.columns.clear()

        if not self.jsonlines:
            try:
                self.reload_json()
            except ValueError as e:
                status('trying jsonl')
                self.jsonlines = True

        if self.jsonlines:
            self.reload_jsonl()

    def reload_json(self):
        self.rows = []
        with self.source.open_text() as fp:
            ret = json.load(fp, object_hook=self.addRow)

        if isinstance(ret, dict):
            self.rows = [ret]
        else:
            self.rows = []
            for row in Progress(ret):
                self.addRow(row)

    def reload_jsonl(self):
        with self.source.open_text() as fp:
            self.rows = []
            for L in fp:
                self.addRow(json.loads(L))

    def addRow(self, row):
        self.rows.append(row)  # just during loading until final assignment
        for k in row:
            if k not in self.colnames:
                c = ColumnItem(k, type=deduceType(row[k]))
                self.colnames[k] = c
                self.addColumn(c)
        return row

@async
def save_json(p, vs):
    def rowdict(cols, row):
        d = {}
        for col in cols:
            try:
                d[col.name] = col.getTypedValue(row)
            except Exception:
                pass
        return d

    with p.open_text(mode='w') as fp:
        vcols = vs.visibleCols
        for chunk in json.JSONEncoder().iterencode([rowdict(vcols, r) for r in Progress(vs.rows)]):
            fp.write(chunk)
