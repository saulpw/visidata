from visidata import *

def open_frictionless(p):
    return FrictionlessIndexSheet(p.name, source=p)

class FrictionlessIndexSheet(IndexSheet):
    @asyncthread
    def reload(self):
        import datapackage
        self.dp = datapackage.Package(self.source.open_text())
        self.rows = []
        for r in Progress(self.dp.resources):
            vs = openSource(self.source.with_name(r.descriptor['path']), filetype=r.descriptor['format'])
            self.addRow(vs)
