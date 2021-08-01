import os
import contextlib
import re

from visidata import options, SequenceSheet, TableSheet, FileExistsError, option, VisiData, ColumnItem

def open_vnl(p):
    return VnlSheet(p.name, source=p)


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


class VnlSheet(TableSheet):
    rowtype = list  # rowdef: list of values

    def iterload(self):

        re_hard_comment = re.compile('^\s*(?:#[#!]|#\s*$|$)')
        re_soft_comment = re.compile('^\s*#\s*(.*?)\s*$')
        re_comment      = re.compile('^\s*(.*?)\s*#')

        got_legend = False

        with self.source.open_text(encoding=self.options.encoding) as fp:

                for line in splitter(fp):
                    if not line or re_hard_comment.match(line):
                        continue

                    if not got_legend:

                        m = re_soft_comment.match(line)
                        # No legend yet. Comments are field labels, data is an
                        # error
                        if m:
                            self.columns = []
                            cols = m.group(1).split()
                            for i in range(len(cols)):
                                self.addColumn(ColumnItem(cols[i], i))
                            got_legend = True
                        else:
                            yield Exception("invalid vnlog data: data line before a legend line")

                    else:
                        # Got a legend already. Comments are comments.
                        m = re_comment.match(line)
                        if m:
                            # throw out comment and leading/trailing whitespace
                            line = m.group(1)
                        else:
                            # throw out leading/trailing whitespace
                            line = line.strip()

                        if not line:
                            continue

                        row = [None if x == "-" else x for x in line.split()]

                        if len(row) < self.nVisibleCols:
                            # extend rows that are missing entries
                            row.extend([None]*(self.nVisibleCols-len(row)))

                        yield row

@VisiData.api
def save_vnl(vd, p, vs):
    'Write sheet to file `fn` as VNL.'

    def sanitize(s):
        # Remove leading,trailing whitespace; replace interstitial whitespace
        # with _
        s = s.strip()
        if len(s) == 0:
            return '-'
        return re.sub(r"\s", '_', s)

    with p.open_text(mode='w', encoding=vs.options.encoding) as fp:
        cols = vs.visibleCols
        fp.write('# ')
        fp.write(' '.join(sanitize(c.name) for c in cols))
        fp.write('\n')

        for dispvals in vs.iterdispvals(format=True):
            vals = dispvals.values()
            fp.write(' '.join(sanitize(v) for v in vals))
            fp.write('\n')

    vd.status('%s save finished' % p)
