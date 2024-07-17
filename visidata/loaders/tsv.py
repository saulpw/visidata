import os
import contextlib
import itertools
import collections
import math
import time

from visidata import vd, asyncthread, options, Progress, ColumnItem, SequenceSheet, Sheet, VisiData
from visidata import namedlist, filesize

vd.option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
vd.option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
vd.option('tsv_safe_newline', '\u001e', 'replacement for newline character when saving to tsv', replay=True)
vd.option('tsv_safe_tab', '\u001f', 'replacement for tab character when saving to tsv', replay=True)


@VisiData.api
def open_tsv(vd, p):
    return TsvSheet(p.base_stem, source=p)


def adaptive_bufferer(fp, max_buffer_size=65536):
    """Loading e.g. tsv files goes faster with a large buffer. But when the input stream
    is slow (e.g. 1 byte/second) and the buffer size is large, it can take a long time until
    the buffer is filled. Only when the buffer is filled (or the input stream is finished)
    you can see the data visualized in visidata. That's why we use an adaptive buffer.
    For fast input streams, the buffer becomes large, for slow input streams, the buffer stays
    small"""
    buffer_size = 8
    processed_buffer_size = 0
    previous_start_time = time.time()
    while True:
        next_chunk = fp.read(max(buffer_size, 1))
        if not next_chunk:
            break

        yield next_chunk

        processed_buffer_size += len(next_chunk)

        current_time = time.time()
        current_delta = current_time - previous_start_time

        if current_delta < 1:
            # if it takes less than one second to fill the buffer, double the size of the buffer
            buffer_size = min(buffer_size * 2, max_buffer_size)
        else:
            # if it takes longer than one second, decrease the buffer size so it takes about
            # 1 second to fill it
            previous_start_time = current_time
            buffer_size = math.ceil(min(processed_buffer_size / current_delta, max_buffer_size))
            processed_buffer_size = 0

def splitter(stream, delim='\n'):
    'Generates one line/row/record at a time from stream, separated by delim'

    buf = type(delim)()

    for chunk in stream:
        buf += chunk

        *rows, buf = buf.split(delim)
        yield from rows

    buf = buf.rstrip(delim)  # trim empty trailing lines
    if buf:
        yield from buf.rstrip(delim).split(delim)


# rowdef: list
class TsvSheet(SequenceSheet):
    delimiter = ''
    row_delimiter = ''

    def iterload(self):
        delim = self.delimiter or self.options.delimiter
        rowdelim = self.row_delimiter or self.options.row_delimiter
        if delim == '':
            vd.warning("using '\\x00' as field delimiter")
            delim = '\x00'  #2272
            self.options.regex_skip = ''
        if rowdelim == '':
            vd.warning("using '\\x00' as row delimiter")
            rowdelim = '\x00'
            self.options.regex_skip = ''
        if delim == rowdelim:
            vd.fail('field delimiter and row delimiter cannot be the same')

        with self.open_text_source() as fp:
                regex_skip = getattr(fp, '_regex_skip', None)
                for line in splitter(adaptive_bufferer(fp), rowdelim):
                    if not line or (regex_skip and regex_skip.match(line)):
                        continue

                    row = line.split(delim)

                    if len(row) < self.nVisibleCols:
                        # extend rows that are missing entries
                        row.extend([None]*(self.nVisibleCols-len(row)))

                    yield row


@VisiData.api
def save_tsv(vd, p, vs, delimiter='', row_delimiter=''):
    'Write sheet to file `fn` as TSV.'
    unitsep = delimiter or vs.options.delimiter
    rowsep = row_delimiter or vs.options.row_delimiter
    if unitsep == '':
        vd.warning("saving with '\\x00' as field delimiter")
        unitsep = '\x00'
    if rowsep == '':
        vd.warning("saving with '\\x00' as row delimiter")
        rowsep = '\x00'
    if unitsep == rowsep:
        vd.fail('field delimiter and row delimiter cannot be the same')
    trdict = vs.safe_trdict()

    with p.open(mode='w', encoding=vs.options.save_encoding) as fp:
        colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + rowsep
        fp.write(colhdr)

        for dispvals in vs.iterdispvals(format=True):
            fp.write(unitsep.join(dispvals.values()))
            fp.write(rowsep)


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

        with vs.source.open(mode='w') as fp:
            colhdr = unitsep.join(col.name.translate(trdict) for col in vs.visibleCols) + vs.options.row_delimiter
            if colhdr.strip():  # is anything but whitespace
                fp.write(colhdr)

    newrow = ''

    contents = vs.source.open(mode='r').read()
    if not contents.endswith('\n'):  #1569
        newrow += '\n'

    newrow += '\t'.join(col.getDisplayValue(row) for col in vs.visibleCols) + '\n'

    with vs.source.open(mode='a') as fp:
        fp.write(newrow)


vd.addGlobals({
    'TsvSheet': TsvSheet,
})
