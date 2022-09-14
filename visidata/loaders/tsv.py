"""You can use this loader to use visidata in mysql (or mycli) client. Use the following config to enable
visidata by default in the mysql client:

Edit ~/.my.cnf:
[mysql]
silent
pager=pager=vd --disable-universal-newline=1 --interpret_escaped_chars=1 -f tsv
"""

import os
import codecs
import contextlib
import itertools
import collections
import io

from visidata import vd, asyncthread, options, Progress, ColumnItem, SequenceSheet, Sheet, FileExistsError, getType, VisiData, RepeatFile
from visidata import namedlist, filesize

vd.option('delimiter', '\t', 'field delimiter to use for tsv/usv filetype', replay=True)
vd.option('row_delimiter', '\n', 'row delimiter to use for tsv/usv filetype', replay=True)
vd.option('disable_universal_newline', False, 'causes strict interpretaion of newlines', replay=True)
vd.option('interpret_escaped_chars', False, 'enable interpretation of backslash escapes', replay=True)
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
        disable_inversal_newline = bool(self.options.disable_universal_newline)
        interpret_escaped_chars = bool(self.options.interpret_escaped_chars)

        if disable_inversal_newline:
            fp = self.source.open_bytes()
        else:
            fp = self.source.open_text(encoding=self.options.encoding)

        if disable_inversal_newline:
            fp = io.TextIOWrapper(fp, encoding=options.encoding, errors=options.encoding_errors, newline=rowdelim)

        with fp:
            for line in splitter(fp, rowdelim):
                if not line:
                    continue

                if interpret_escaped_chars:
                    row = list(s.encode("utf-8", errors=options.encoding_errors).decode("unicode_escape", errors=options.encoding_errors) for s in line.split(delim))
                else:
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
