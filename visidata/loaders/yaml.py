from visidata import *


class YamlSheet(Sheet):
    def iterload(self):
        import yaml
        with self.source.open_text() as fp:
            rows = yaml.load(fp, Loader=yaml.FullLoader)
        if not isinstance(rows, list):
            yield rows
        else:
            yield from rows

        row = self.rows[0]
        self.columns = []
        for k in row:
            c = ColumnItem(k, type=deduceType(row[k]))
            self.addColumn(c)


vd.filetype('yml', YamlSheet)
vd.filetype('yaml', YamlSheet)
