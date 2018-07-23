import os
import contextlib

from visidata import asyncthread, options, Progress, status, ColumnItem, Sheet
from visidata import namedlist


def _getTsvHeaders(fp, nlines):
    return [L.split(options.delimiter) for L in getlines(fp, nlines or -1)]

def getlines(fp, maxlines=None):
    i = 0
    while True:
        if maxlines is not None and i >= maxlines:
            break

        try:
            L = next(fp)
        except StopIteration:
            break

        L = L.rstrip('\n')
        if L:
            yield L
        i += 1


def open_tsv(p):
    return TsvSheet(p.name, source=p)


# rowdef: namedlist
class TsvSheet(Sheet):
    _rowtype = None
    @asyncthread
    def reload(self):
        self.reload_sync()

    def reload_sync(self):
        'Perform synchronous loading of TSV file, discarding header lines.'
        header_lines = options.get('header', self)

        with self.source.open_text() as fp:
            headers = _getTsvHeaders(fp, header_lines) # or 1)  # get one data line if no headers

            self.columns = [
                    ColumnItem('\\n'.join(x), i)
                        for i, x in enumerate(zip(*headers[:header_lines]))
                    ]
            self._rowtype = namedlist('tsvobj', [c.name for c in self.columns])

            self.recalc()
            delim = options.delimiter
            self.rows = []

            with Progress(total=self.source.filesize) as prog:
                for L in getlines(fp):
                    row = L.split(delim)
                    ncols = self._rowtype.length()  # current number of cols
                    if len(row) > ncols:
                        newcols = [ColumnItem('', len(row)+i, width=8) for i in range(len(row)-ncols)]
                        self._rowtype = namedlist(self._rowtype.__name__, list(self._rowtype._fields) + ['_' for c in newcols])
                    self.addRow(self._rowtype(row))
                    prog.addProgress(len(L))


def tsv_trdict(delim=None):
    'returns string.translate dictionary for replacing tabs and newlines'
    delim = delim or options.delimiter
    return {ord(delim): options.tsv_safe_tab, # \t
            10: options.tsv_safe_newline,  # \n
            13: options.tsv_safe_newline,  # \r
            }


def save_tsv_header(p, vs):
    'Write tsv header for Sheet `vs` to Path `p`.'
    trdict = tsv_trdict()
    delim = options.delimiter

    with p.open_text(mode='w') as fp:
        colhdr = delim.join(col.name.translate(trdict) for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)


@asyncthread
def save_tsv(p, vs):
    'Write sheet to file `fn` as TSV.'
    delim = options.delimiter
    trdict = tsv_trdict()

    save_tsv_header(p, vs)

    with p.open_text(mode='a') as fp:
        if trdict:
            for r in Progress(vs.rows):
                fp.write(delim.join(col.getDisplayValue(r).translate(trdict) for col in vs.visibleCols) + '\n')
        else:
            for r in Progress(vs.rows):
                fp.write(delim.join(col.getDisplayValue(r) for col in vs.visibleCols) + '\n')

    status('%s save finished' % p)


def append_tsv_row(vs, row):
    'Append `row` to vs.source, creating file with correct headers if necessary. For internal use only.'
    if not vs.source.exists():
        with contextlib.suppress(FileExistsError):
            parentdir = vs.source.parent.resolve()
            if parentdir:
                os.makedirs(parentdir)

        save_tsv_header(vs.source, vs)

    trdict = tsv_trdict(delim='\t')

    with vs.source.open_text(mode='a') as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')
