import collections

from visidata import VisiData, Sheet, ItemColumn


@VisiData.api
def open_lsv(vd, p):
    return LsvSheet(p.name, source=p)


@VisiData.api
def save_lsv(vd, p, *vsheets):
    vs = vsheets[0]
    with p.open_text(mode='w', encoding=vs.options.encoding) as fp:
        for row in vs.iterrows():
            for col in vs.visibleCols:
                fp.write('%s: %s\n' % (col.name, col.getDisplayValue(row)))
            fp.write('\n')


class LsvSheet(Sheet):
    def addRow(self, row, **kwargs):
        super().addRow(row, **kwargs)
        for k in row:
            if k not in self._knownCols:
                self.addColumn(ItemColumn(k))
                self._knownCols.add(k)


    def iterload(self):
        self.columns = []
        self.rows = []
        self._knownCols = set()
        row = collections.defaultdict(str)
        k = ''
        for line in self.source.open_text():
            line = line.strip()
            if not line:
                yield row
                row = collections.defaultdict(str)

            if ':' in line:
                k, line = line.split(':', maxsplit=1)
            # else append to previous k

            row[k.strip()] += line.strip()

        if row:
            yield row
