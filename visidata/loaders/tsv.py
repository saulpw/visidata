import os
import contextlib
import itertools
import collections

from visidata import vd, asyncthread, options, Progress, ColumnItem, SequenceSheet, Sheet, FileExistsError, getType, VisiData
from visidata import namedlist, filesize

vd.option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
vd.option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
vd.option('tsv_safe_newline', '\u001e', 'replacement for newline character when saving to tsv', replay=True)
vd.option('tsv_safe_tab', '\u001f', 'replacement for tab character when saving to tsv', replay=True)


@VisiData.api
def open_tsv(vd, p):
    return TsvSheet(p.name, source=p)


def splitter(fp, delim='\n'):
    'Generates one line/row/record at a time from fp, separated by delim'

    buf = ''
    while True:
        nextbuf = fp.read(65536)
        if not nextbuf:
            break
        buf += nextbuf

        *rows, buf = buf.split(delim)
        yield from rows

    yield from buf.rstrip(delim).split(delim)


# rowdef: list
class TsvSheet(SequenceSheet):
    delimiter = ''
    row_delimiter = ''

    def iterload(self):
        delim = self.delimiter or self.options.delimiter
        rowdelim = self.row_delimiter or self.options.row_delimiter

        with self.source.open_text(encoding=self.options.encoding) as fp:
                for line in splitter(fp, rowdelim):
                    if not line:
                        continue

                    row = list(line.split(delim))

                    if len(row) < self.nVisibleCols:
                        # extend rows that are missing entries
                        row.extend([None]*(self.nVisibleCols-len(row)))

                    yield row


@VisiData.api
def save_tsv(vd, p, vs, delimiter='', row_delimiter=''):
    'Write sheet to file `fn` as TSV.'
    unitsep = delimiter or vs.options.delimiter
    rowsep = row_delimiter or vs.options.row_delimiter
    trdict = vs.safe_trdict()

    with p.open_text(mode='w', encoding=vs.options.encoding) as fp:
        colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + rowsep
        fp.write(colhdr)

        for dispvals in vs.iterdispvals(format=True):
            fp.write(unitsep.join(dispvals.values()))
            fp.write(rowsep)

    vd.status('%s save finished' % p)


@Sheet.api
def append_tsv_row(vs, row):
    'Append `row` to vs.source, creating file with correct headers if necessary. For internal use only.'
    if not vs.source.exists():
        with contextlib.suppress(FileExistsError):
            parentdir = vs.source.parent
            if parentdir:
                os.makedirs(parentdir)

        # Write tsv header for Sheet `vs` to Path `p`
        trdict = vs.safe_trdict()
        unitsep = options.delimiter

        with vs.source.open_text(mode='w', encoding=vs.options.encoding) as fp:
            colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + vs.options.row_delimiter
            if colhdr.strip():  # is anything but whitespace
                fp.write(colhdr)

    with vs.source.open_text(mode='a', encoding=vs.options.encoding) as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')


vd.addGlobals({
    'TsvSheet': TsvSheet,
})
