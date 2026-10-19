'Custom VisiData save format'

import json

from visidata import vd, VisiData, JsonSheet, Progress, IndexSheet, SettableColumn, ItemColumn, ExprColumn


NL='\n'

@VisiData.api
def open_vds(vd, p):
    return VdsIndexSheet(p.base_stem, source=p)


def _colstate(col):
    '''Return the .vds metadata dict for *col*.

    A column type is only preserved if it can actually be reconstructed on load:
    its class must be in the global namespace, and its saved state must be
    JSON-serializable.  Anything else (JoinKeyColumn, SubColumnFunc, ...) is
    saved as a plain Column holding the values by name  #3175.'''
    d = col.__getstate__()
    if not isinstance(col, (SettableColumn, ItemColumn)):
        clsname = type(col).__name__
        if clsname in vd.getGlobals():
            try:
                json.dumps(d)
            except TypeError:
                pass
            else:
                d['col'] = clsname
                return d

    d['col'] = 'Column'
    d['expr'] = col.name  #2037  override expr
    return d


@VisiData.api
def save_vds(vd, p, *sheets):
    'Save in custom VisiData format, preserving columns and their attributes.'

    with p.open(mode='w', encoding='utf-8') as fp:
        for vs in sheets:
            # class and attrs for vs
            d = { 'name': vs.name, }
            fp.write('#'+json.dumps(d)+NL)

            # class and attrs for each column in vs
            rowkeys = {}  # col -> unique key in each row dict
            for col in vs.columns:
                key, n = col.name, 1
                while key in rowkeys.values():
                    n += 1
                    key = f'{col.name}_{n}'
                rowkeys[col] = key
                d = _colstate(col)
                if key != col.name:
                    d['key'] = key  #3146
                fp.write('#'+json.dumps(d)+NL)

            if not vs.rows:
                fp.write(NL)  #2342  blank line to separate sheets without rows
                continue

            with Progress(gerund='saving'):
                for row in vs.iterdispvals(*vs.columns, format=False):
                    d = {rowkeys[col]:val for col, val in row.items()}
                    fp.write(json.dumps(d, default=str)+NL)


class VdsIndexSheet(IndexSheet):
    stackRestored = False

    def iterload(self):
        vs = None
        with self.source.open(encoding='utf-8') as fp:
            line = fp.readline()
            while line:
                if line.startswith('#{'):
                    d = json.loads(line[1:])
                    if 'col' not in d:
                        vs = VdsSheet(d.pop('name'), columns=[], source=self, source_fpos=fp.tell())
                        yield vs
                line = fp.readline()

    def afterLoad(self):
        super().afterLoad()
        if not self.stackRestored and self.rows and self in vd.sheets:
            self.stackRestored = True
            self.restoreStack()

    def restoreStack(self):
        'Replace this sheet on the sheets stack with its sheets, first sheet on top, as save-all wrote them.'
        for vs in self.rows:
            vs.vd = vd
            vs.pane = self.pane
            if vs.precious and vs not in vd.allSheets:
                vd.allSheets.append(vs)
        i = vd.sheets.index(self)
        vd.sheets[i:i+1] = self.rows  #2309


class VdsSheet(JsonSheet):
    def newRow(self):
        return {}   # rowdef: dict

    def iterload(self):
        self.colnames = {}
        self.columns = []

        with self.source.source.open(encoding='utf-8') as fp:
            fp.seek(self.source_fpos)

            # consume all metadata, create columns
            line = fp.readline()
            while line and line.startswith('#{'):
                d = json.loads(line[1:])
                if 'col' not in d:
                    raise Exception(d)
                classname = d.pop('col')
                if classname == 'Column':
                    classname = 'ItemColumn'
                    d['expr'] = d.get('key', d['name'])
                key = d.pop('key', d['name'])

                c = vd.getGlobals()[classname](d.pop('name'), sheet=self)
                self.addColumn(c)
                self.colnames[key] = c
                self._knownKeys.add(key)
                c.__setstate__(d)  # must happen after addColumn sets .sheet

                line = fp.readline()

            while line and not line.startswith('#{'):
                d = json.loads(line)
                yield d
                line = fp.readline()

vd.addGlobals(VdsIndexSheet=VdsIndexSheet, VdsSheet=VdsSheet)
