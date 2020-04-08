from visidata import *

__all__ = ['openurl_postgres', 'PgTable', 'PgTablesSheet']

def codeToType(type_code, colname):
    import psycopg2
    try:
        tname = psycopg2._psycopg.string_types[type_code].name
        if 'INTEGER' in tname:
            return int
        if 'STRING' in tname:
            return str
    except KeyError:
        status('unknown postgres type_code %s for %s' % (type_code, colname))
    return anytype


def openurl_postgres(url, filetype=None):
    import psycopg2

    url = urlparse(url.given)

    if url.scheme != 'postgres':
        error('postgres loader requires a postgres url scheme')

    conn = psycopg2.connect(
                user=url.netloc.split(':')[0],
                dbname=url.path[1:],
                host=url.netloc.split(':')[1].split('@')[1],
                port=url.netloc.split(':')[-1],
                password=url.netloc.split(':')[1].split('@')[0])

    return PgTablesSheet(dbname+"_tables", sql=SQL(conn))


class SQL:
    def __init__(self, conn):
        self.conn = conn

    def cur(self, qstr):
        randomname = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        cur = self.conn.cursor(randomname)
        cur.execute(qstr)
        return cur

    @asyncthread
    def query_async(self, qstr, callback=None):
        with self.cur(qstr) as cur:
            callback(cur)
            cur.close()


def cursorToColumns(cur):
    cols = []
    for i, coldesc in enumerate(cur.description):
        c = ColumnItem(coldesc.name, i, type=codeToType(coldesc.type_code, coldesc.name))
        cols.append(c)
    return cols



# rowdef: (table_name, ncols)
class PgTablesSheet(Sheet):
    rowtype = 'tables'

    def reload(self):
        qstr = "SELECT table_name, COUNT(column_name) AS ncols FROM information_schema.columns WHERE table_schema = 'public' GROUP BY table_name"

        with self.sql.cur(qstr) as cur:
            self.nrowsPerTable = {}

            self.rows = []
            # try to get first row to make cur.description available
            r = cur.fetchone()
            if r:
                self.addRow(r)
            self.columns = cursorToColumns(cur)
            self.setKeys(self.columns[0:1])  # table_name is the key
            self.addColumn(Column('nrows', type=int, getter=lambda col,row: col.sheet.getRowCount(row[0])))

            for r in cur:
                self.addRow(r)

    def setRowCount(self, cur):
        result = cur.fetchall()
        tablename = result[0][0]
        self.nrowsPerTable[tablename] = result[0][1]

    def getRowCount(self, tablename):
        if tablename not in self.nrowsPerTable:
            thread = self.sql.query_async("SELECT '%s', COUNT(*) FROM %s" % (tablename, tablename), callback=self.setRowCount)
            self.nrowsPerTable[tablename] = thread

        return self.nrowsPerTable[tablename]

# rowdef: tuple of values as returned by fetchone()
class PgTable(Sheet):
    @asyncthread
    def reload(self):
        with self.sql.cur("SELECT * FROM " + self.source) as cur:
            self.rows = []
            r = cur.fetchone()
            if r:
                self.addRow(r)
            self.columns = cursorToColumns(cur)
            for r in cur:
                self.addRow(r)

PgTablesSheet.addCommand(ENTER, 'dive-row', 'vd.push(PgTable(name+"."+cursorRow[0], source=cursorRow[0], sql=sql))', 'open postgres table in current row')
