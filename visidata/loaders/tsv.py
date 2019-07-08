import os
import contextlib
import itertools
import collections

from visidata import asyncthread, options, Progress, status, ColumnItem, Sheet, FileExistsError, getType, exceptionCaught, option
from visidata import namedlist, filesize

option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
option('tsv_safe_newline', '\u001e', 'replacement for newline character when saving to tsv', replay=True)
option('tsv_safe_tab', '\u001f', 'replacement for tab character when saving to tsv', replay=True)


def splitter(fp, delim='\n'):
    'Generates one line/row/record at a time from fp, separated by delim'

    remainder = ''
    while True:
        nextbuf = fp.read(512)
        if not nextbuf:
            if remainder:
                yield remainder
            break
        buf = remainder + nextbuf
        rows = buf.split(delim)
        if buf[-1] != delim:
            remainder = rows[-1]
            yield from rows[:-1]
        else:
            remainder = ''
            yield from rows


def getlines(iter, maxlines=None, delim='\n'):
    i = 0

    while True:
        if maxlines is not None and i >= maxlines:
            break

        try:
            L = next(iter)
        except StopIteration:
            break

        L = L.rstrip(delim)
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
        delim = options.get('delimiter', self)
        rowdelim = options.get('row_delimiter', self)


        with self.source.open_text() as fp:
            rdr = splitter(fp, rowdelim)

            # get one line anyway to determine number of columns
            lines = list(getlines(rdr, int(header_lines) or 1, rowdelim))
            headers = [L.split(delim) for L in lines]

            if header_lines <= 0:
                self.columns = [ColumnItem('', i) for i in range(len(headers[0]))]
            else:
                self.columns = [
                    ColumnItem('\\n'.join(x), i)
                        for i, x in enumerate(zip(*headers[:header_lines]))
                    ]

            lines = lines[header_lines:]  # in case of header_lines == 0
            self._rowtype = namedlist('tsvobj', [c.name for c in self.columns])

            self.recalc()
            self.rows = []

            with Progress(total=filesize(self.source)) as prog:
                for L in itertools.chain(lines, getlines(rdr, delim=rowdelim)):
                    row = L.split(delim)
                    ncols = self._rowtype.length()  # current number of cols
                    if len(row) > ncols:
                        # add unnamed columns to the type not found in the header
                        newcols = [ColumnItem('', len(row)+i, width=8) for i in range(len(row)-ncols)]
                        self._rowtype = namedlist(self._rowtype.__name__, list(self._rowtype._fields) + ['_' for c in newcols])
                        for c in newcols:
                            self.addColumn(c)
                    elif len(row) < ncols:
                        # extend rows that are missing entries
                        row.extend([None]*(ncols-len(row)))

                    self.addRow(self._rowtype(row))
                    prog.addProgress(len(L))

    def newRow(self):
        return self._rowtype()

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


def genAllValues(rows, cols, trdict={}, format=True):
    transformers = collections.OrderedDict()  # list of transformers for each column in order
    for col in cols:
        transformers[col] = [ col.type ]
        if format:
            transformers[col].append(
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
            parentdir = vs.source.parent.resolve()
            if parentdir:
                os.makedirs(parentdir)

        save_tsv_header(vs.source, vs)

    with vs.source.open_text(mode='a') as fp:
        fp.write('\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n')
