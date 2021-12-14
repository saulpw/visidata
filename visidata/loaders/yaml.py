from itertools import chain

from visidata import VisiData, Progress, JsonSheet


@VisiData.api
def open_yml(vd, p):
    return YamlSheet(p.name, source=p)

VisiData.open_yaml = VisiData.open_yml

class YamlSheet(JsonSheet):
    def iterload(self):
        import yaml
        with self.source.open_text() as fp:
            documents = yaml.safe_load_all(fp)

            self.columns = []
            self._knownKeys.clear()

            # Peek at the document stream to determine how to best DWIM.
            #
            # This code is a bit verbose because it avoids slurping the generator
            # all at once into memory.
            try:
                first = next(documents)
            except StopIteration:
                # Empty file‽
                yield None
                return

            try:
                second = next(documents)
            except StopIteration:
                if isinstance(first, list):
                    # A file with a single YAML list: yield one row per list item.
                    yield from Progress(first)
                else:
                    # A file with a single YAML non-list value, e.g a dict.
                    yield first
            else:
                # A file containing multiple YAML documents: yield one row per document.
                yield from Progress(chain([first, second], documents), total=0)
