from visidata import *


class FrictionlessIndexSheet(IndexSheet):
    def iterload(self):
        import datapackage
        self.dp = datapackage.Package(self.source.open_text())
        for r in Progress(self.dp.resources):
            yield openSource(self.source.with_name(r.descriptor['path']), filetype=r.descriptor['format'])

vd.filetype('frictionless', FrictionlessIndexSheet)
