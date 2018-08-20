from visidata import *

def open_yaml(p):
    return YamlSheet(p.name, source=p)

open_yml = open_yaml

class YamlSheet(Sheet):
    @asyncthread
    def reload(self):
        import yaml
        with self.source.open_text() as fp:
            self.rows = yaml.load(fp)
        self.columns = []
        for k in self.rows[0]:
            c = ColumnItem(k, type=deduceType(self.rows[0][k]))
            self.addColumn(c)
