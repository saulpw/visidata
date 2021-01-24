'Custom VisiData save format'

import json
from visidata import *

NL='\n'

@VisiData.api
def open_vds(vd, p):
    return VdsIndexSheet(p.name, source=p)


@VisiData.api
def save_vds(vd, p, *sheets):
    'Save in custom VisiData format, preserving columns and their attributes.'

    with p.open_text(mode='w') as fp:
        for vs in sheets:
            # class and attrs for vs
            d = { 'name': vs.name, }
            fp.write('#'+json.dumps(d)+NL)

            # class and attrs for each column in vs
            for col in vs.visibleCols:
                d = col.__getstate__()
                d['col'] = type(col).__name__
                fp.write('#'+json.dumps(d)+NL)

            with Progress(gerund='saving'):
                for row in vs.iterdispvals(*vs.visibleCols, format=True):
                    d = {col.name:val for col, val in row.items()}
                    fp.write(json.dumps(d)+NL)


class VdsIndexSheet(IndexSheet):
    def iterload(self):
        vs = None
        with self.source.open_text() as fp:
            line = fp.readline()
            while line:
                if line.startswith('#{'):
                    d = json.loads(line[1:])
                    if 'col' not in d:
                        vs = VdsSheet(d.pop('name'), columns=[], source=self.source, source_fpos=fp.tell())
                        yield vs
                line = fp.readline()


class VdsSheet(Sheet):
    def newRow(self):
        return {}   # rowdef: dict

    def iterload(self):
        self.colnames = {}
        self.columns = []

        with self.source.open_text() as fp:
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
                    d['expr'] = d['name']

                c = globals()[classname](d.pop('name'))
                self.colnames[c.name] = c
                self.addColumn(c)
                for k, v in d.items():
                    setattr(c, k, v)

                line = fp.readline()

            while line and not line.startswith('#{'):
                d = json.loads(line)
                yield d
                line = fp.readline()
