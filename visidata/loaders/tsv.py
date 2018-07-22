import os
import contextlib

from visidata import asyncthread, options, Progress, status, ColumnItem, Sheet


def _getTsvHeaders(fp, nlines):
    headers = []
    i = 0
    while i < nlines:
        try:
            L = next(fp)
        except StopIteration:  # not enough lines for headers
            return headers
        L = L.rstrip('\n')
        if L:
            headers.append(L.split(options.delimiter))
            i += 1

    return headers


def open_tsv(p, vs=None):
    'Parse contents of Path `p` and populate columns.'

    if vs is None:
        vs = TsvSheet(p.name, source=p)

    return vs


class TsvSheet(Sheet):
    @asyncthread
    def reload(self):
        header_lines = int(options.header)

        with self.source.open_text() as fp:
            headers = _getTsvHeaders(fp, header_lines or 1)  # get one data line if no headers

            if header_lines == 0:
                self.columns = [ColumnItem('', i, width=8) for i in range(len(headers[0]))]
                # columns ideally reflect the max number of fields over all rows
                # but that's a lot of work for a large dataset
            else:
                self.columns = [
                    ColumnItem('\\n'.join(x), i)
                        for i, x in enumerate(zip(*headers[:header_lines]))
                    ]

        self.recalc()

        reload_tsv_sync(self)


def reload_tsv_sync(vs, **kwargs):
    'Perform synchronous loading of TSV file, discarding header lines.'
    header_lines = kwargs.get('header', options.header)

    delim = options.delimiter
    vs.rows = []
    with vs.source.open_text() as fp:
        _getTsvHeaders(fp, header_lines)  # discard header lines

        with Progress(total=vs.source.filesize) as prog:
            while True:
                try:
                    L = next(fp)
                except StopIteration:
                    break
                L = L.rstrip('\n')
                if L:
                    vs.addRow(L.split(delim))
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
