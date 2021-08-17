"""Loader to use visidata in mysql (or mycli) client. Use the following config to enable
visidata by default in the mysql client:

Edit ~/.my.cnf:
[mysql]
silent
pager=vd -f mysqlclient
"""

from visidata import SequenceSheet
import io


def load_mysqlclient(fn):
    vs = open_mysqlclient(Path(fn))
    yield from vs.iterload()

def open_mysqlclient(p):
    return MysqlClientSheet(p.name, source=p)

def _mysqlclient_split_lines(fp):
    buf = ''
    while True:
        nextbuf = fp.readline()
        if not nextbuf:
            break
        buf += nextbuf

        *rows, buf = buf.split("\n")
        yield from rows

    yield from buf.split("\n")


# rowdef: list
class MysqlClientSheet(SequenceSheet):
    def iterload(self):
        with io.TextIOWrapper(self.source.open("rb"), errors="replace", newline="\n", encoding=self.options.getonly('encoding', 'global', 'utf-8')) as fp:
            for line in _mysqlclient_split_lines(fp):
                if not line:
                    continue

                row = [r.replace("\\\\", "\\ ").replace("\\n", "\n").replace("\\0", "\0").replace("\\t", "\t").replace("\\ ", "\\") for r in line.split("\t")]

                if len(row) < self.nVisibleCols:
                    # extend rows that are missing entries
                    row.extend([None]*(self.nVisibleCols-len(row)))

                yield row
