import os
import contextlib
import itertools

from visidata import asyncthread, options, Progress, status, ColumnItem, Sheet, FileExistsError, getType, exceptionCaught
from visidata.namedlist import namedlist


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
        delim = options.get('delimiter', self)

        with self.source.open_text() as fp:
            # get one line anyway to determine number of columns
            lines = list(getlines(fp, int(header_lines) or 1))
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

            with Progress(total=self.source.filesize) as prog:
                for L in itertools.chain(lines, getlines(fp)):
                    row = L.split(delim)
                    ncols = self._rowtype.length()  # current number of cols
                    if len(row) > ncols:
                        # add unnamed columns to the type not found in the header
                        newcols = [ColumnItem('', len(row)+i, width=8) for i in range(len(row)-ncols)]
                        self._rowtype = namedlist(self._rowtype.__name__, list(self._rowtype._fields) + ['_' for c in newcols])
                        for c in newcols:
                            self.addColumn(c)
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
    delim = options.delimiter

    with p.open_text(mode='w') as fp:
        colhdr = delim.join(col.name.translate(trdict) for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)


@asyncthread
def save_tsv(p, vs):
    'Write sheet to file `fn` as TSV.'
    delim = options.get('delimiter', vs)
    trdict = tsv_trdict(vs)

    save_tsv_header(p, vs)
    save_errors = options.get('save_errors', vs)

    transformers = []  # list of transformers for each column in order
    for col in vs.visibleCols:
        transforms = [col.getValue, col.type, lambda v,fmtfunc=getType(col.type).formatter,fmtstr=col.fmtstr: fmtfunc(fmtstr, '' if v is None else v)]
        if trdict:
            transforms.append(lambda v,trdict=trdict: v.translate(trdict))
        transformers.append(transforms)

    with p.open_text(mode='a') as fp:
        for r in Progress(vs.rows):
            dispvals = []
            for transforms in transformers:
                try:
                    dispval = r
                    for t in transforms:
                        dispval = t(dispval)
                except Exception as e:
                    exceptionCaught(e)
                    dispval = str(e) if save_errors else ''

                dispvals.append(dispval)
            fp.write(delim.join(dispvals) + '\n')

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
