import os
import contextlib
import itertools
import collections

from visidata import asyncthread, options, Progress, status, ColumnItem, SequenceSheet, Sheet, FileExistsError, getType, exceptionCaught, option
from visidata import namedlist, filesize

option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
option('tsv_safe_newline', '\u001e', 'replacement for newline character when saving to tsv', replay=True)
option('tsv_safe_tab', '\u001f', 'replacement for tab character when saving to tsv', replay=True)


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


def open_tsv(p):
    return TsvSheet(p.name, source=p)


# rowdef: list
class TsvSheet(SequenceSheet):
    def iterload(self):
        delim = options.get('delimiter', self)
        rowdelim = options.get('row_delimiter', self)

        with self.source.open_text() as fp:
            with Progress(total=filesize(self.source)) as prog:
                for line in splitter(fp, rowdelim):
                    if not line:
                        continue

                    prog.addProgress(len(line))
                    row = list(line.split(delim))

                    if len(row) < self.nCols:
                        # extend rows that are missing entries
                        row.extend([None]*(self.nCols-len(row)))

                    yield row


def tsv_trdict(vs):
    'returns string.translate dictionary for replacing tabs and newlines'
    if options.safety_first:
        delim = options.get('delimiter', vs)
        return {ord(delim): options.get('tsv_safe_tab', vs), # \t
            10: options.get('tsv_safe_newline', vs),  # \n
            13: options.get('tsv_safe_newline', vs),  # \r
            }
    return {}

def save_tsv_header(p, vs):
    'Write tsv header for Sheet `vs` to Path `p`.'
    trdict = tsv_trdict(vs)
    unitsep = options.delimiter

    with p.open_text(mode='w') as fp:
        colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + options.row_delimiter
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)


def load_tsv(fn):
    vs = open_tsv(Path(fn))
    yield from vs.iterload()


def genAllValues(rows, cols, trdict={}, format=True):
    transformers = collections.OrderedDict()  # list of transformers for each column in order
    for col in cols:
        transformers[col] = [ col.type ]
        if format:
            transformers[col].append(
                # optimization: only lookup fmtstr once (it may have to get an option value)
                lambda v,fmtfunc=getType(col.type).formatter,fmtstr=col.fmtstr: fmtfunc(fmtstr, '' if v is None else v)
            )
        if trdict:
            transformers[col].append(lambda v,trdict=trdict: v.translate(trdict))

    options_safe_error = options.safe_error
    for r in Progress(rows):
        dispvals = []
        for col, transforms in transformers.items():
            try:
                dispval = col.getValue(r)
            except Exception as e:
                exceptionCaught(e)
                dispval = options_safe_error or str(e)

            try:
                for t in transforms:
                    if dispval is None:
                        dispval = ''
                        break
                    dispval = t(dispval)
            except Exception as e:
                dispval = str(dispval)

            dispvals.append(dispval)

        yield dispvals


@Sheet.api
def save_tsv(vs, p):
    'Write sheet to file `fn` as TSV.'
    unitsep = options.get('delimiter', vs)
    rowsep = options.get('row_delimiter', vs)
    trdict = tsv_trdict(vs)

    save_tsv_header(p, vs)

    with p.open_text(mode='a') as fp:
        for dispvals in genAllValues(vs.rows, vs.visibleCols, trdict, format=True):
            fp.write(unitsep.join(dispvals))
            fp.write(rowsep)

    status('%s save finished' % p)


def append_tsv_row(vs, row):
    'Append `row` to vs.source, creating file with correct headers if necessary. For internal use only.'
    if not vs.source.exists():
        with contextlib.suppress(FileExistsError):
            parentdir = vs.source.parent
            if parentdir:
                os.makedirs(parentdir)

        save_tsv_header(vs.source, vs)

    with vs.source.open_text(mode='a') as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')
