from visidata import *

def open_frictionless(p):
    return FrictionlessIndexSheet(p.name, source=p)

class FrictionlessIndexSheet(IndexSheet):
    def iterload(self):
        import datapackage
        self.dp = datapackage.Package(self.source.open_text())
        for r in Progress(self.dp.resources):
            yield vd.openSource(self.source.with_name(r.descriptor['path']), filetype=r.descriptor['format'])
