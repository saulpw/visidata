import os
import contextlib
import itertools
import collections

from visidata import asyncthread, options, Progress, ColumnItem, SequenceSheet, Sheet, FileExistsError, getType, option, VisiData
from visidata import namedlist, filesize

option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
option('tsv_safe_newline', '\u001e', 'replacement for newline character when saving to tsv', replay=True)
option('tsv_safe_tab', '\u001f', 'replacement for tab character when saving to tsv', replay=True)


def open_tsv(p):
    return TsvSheet(p.name, source=p)

def splitter(fp, delim='\n'):
    'Generates one line/row/record at a time from fp, separated by delim'

    buf = ''
    while True:
        nextbuf = fp.read(512)
        if not nextbuf:
            break
        buf += nextbuf

        *rows, buf = buf.split(delim)
        yield from rows

    yield from buf.rstrip(delim).split(delim)


# rowdef: list
class TsvSheet(SequenceSheet):
    def iterload(self):
        delim = self.options.delimiter
        rowdelim = self.options.row_delimiter

        with self.source.open_text() as fp:
            with Progress(total=filesize(self.source)) as prog:
                for line in splitter(fp, rowdelim):
                    if not line:
                        continue

                    prog.addProgress(len(line))
                    row = list(line.split(delim))

                    if len(row) < self.nVisibleCols:
                        # extend rows that are missing entries
                        row.extend([None]*(self.nVisibleCols-len(row)))

                    yield row


def load_tsv(fn):
    vs = open_tsv(Path(fn))
    yield from vs.iterload()


@VisiData.api
def save_tsv(vd, p, vs):
    'Write sheet to file `fn` as TSV.'
    unitsep = vs.options.delimiter
    rowsep = vs.options.row_delimiter
    trdict = vs.safe_trdict()

    with p.open_text(mode='w') as fp:
        colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + options.row_delimiter
        fp.write(colhdr)

        for dispvals in vs.iterdispvals(format=True):
            fp.write(unitsep.join(dispvals.values()))
            fp.write(rowsep)

    vd.status('%s save finished' % p)


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

        with vs.source.open_text(mode='w') as fp:
            colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + options.row_delimiter
            if colhdr.strip():  # is anything but whitespace
                fp.write(colhdr)

    with vs.source.open_text(mode='a') as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')
