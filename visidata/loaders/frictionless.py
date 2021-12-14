from visidata import VisiData, vd, Progress, IndexSheet

@VisiData.api
def open_frictionless(vd, p):
    return FrictionlessIndexSheet(p.name, source=p)

class FrictionlessIndexSheet(IndexSheet):
    def iterload(self):
        import datapackage
        self.dp = datapackage.Package(self.source.open_text(encoding='utf-8'))
        for r in Progress(self.dp.resources):
            yield vd.openSource(self.source.with_name(r.descriptor['path']), filetype=r.descriptor.get('format', 'json'))
