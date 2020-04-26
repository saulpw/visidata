from visidata import *


class YamlSheet(JsonSheet):
    def iterload(self):
        import yaml
        with self.source.open_text() as fp:
            data = yaml.load(fp, Loader=yaml.FullLoader)

        self.columns = []
        self.colnames = {}

        if not isinstance(data, list):
            yield data
        else:
            yield from Progress(data)


vd.filetype('yml', YamlSheet)
vd.filetype('yaml', YamlSheet)
