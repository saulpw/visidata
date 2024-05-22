#!/usr/bin/env python3

# as plugin: `from viewtsv import open_tsv` in .visidatarc
# standalone: `viewtsv.py <tsv-files>'

from visidata import VisiData, Sheet, ColumnItem, asyncthread, options

@VisiData.api
def open_tsv(vd, p):
    return MinimalTsvSheet(p.base_stem, source=p)


class MinimalTsvSheet(Sheet):
    rowtype = 'rows'

    @asyncthread
    def reload(self):
        self.rows = []

        delim = options.delimiter
        header = True
        with open(self.source, encoding=options.encoding) as fp:
            for line in fp:
                line = line[:-1]  # strip trailing newline

                if header:
                    if delim in line:
                        header = False
                        self.columns = []
                        for i, colname in enumerate(line.split()):
                            self.addColumn(ColumnItem(colname, i))
                    continue

                self.addRow(line.split(delim))


# a minimal main() for standalone apps
if __name__ == '__main__':
    import sys
    from visidata import run, Path, vd
    run(*(vd.open_tsv(Path(fn)) for fn in sys.argv[1:]))
