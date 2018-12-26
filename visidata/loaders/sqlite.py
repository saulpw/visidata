from visidata import ENTER, Sheet, ColumnItem, anytype, status, clean_to_id, Progress, asyncthread, currency, Path

def open_sqlite(path):
    vs = SqliteSheet(path.name + '_tables', path, 'sqlite_master')
    vs.columns = vs.getColumns('sqlite_master')
    vs.addCommand(ENTER, 'dive-row', 'vd.push(SqliteSheet(joinSheetnames(source.name, cursorRow[1]), sheet, cursorRow[1]))')
    return vs
open_db = open_sqlite


class SqliteSheet(Sheet):
    'Provide functionality for importing SQLite databases.'
    def __init__(self, name, pathOrSheet, tableName):
        super().__init__(name, source=pathOrSheet, tableName=tableName)
        if isinstance(pathOrSheet, Sheet):
            self.conn = pathOrSheet.conn
        elif isinstance(pathOrSheet, Path):
            import sqlite3
            self.conn = sqlite3.connect(pathOrSheet.resolve())

    # must not be @asyncthread due to sqlite lib being single-threaded
    def reload(self):
        tblname = self.tableName
        self.columns = self.getColumns(tblname)
        r = self.conn.execute('SELECT COUNT(*) FROM %s' % tblname).fetchall()
        rowcount = r[0][0]
        self.rows = []
        for row in Progress(self.conn.execute("SELECT * FROM %s" % tblname), total=rowcount-1):
            self.addRow(row)

    def getColumns(self, tableName):
        cols = []
        for i, r in enumerate(self.conn.execute('PRAGMA TABLE_INFO(%s)' % tableName)):
            c = ColumnItem(r[1], i)
            t = r[2].lower()
            if t == 'integer':
                c.type = int
            elif t == 'text':
                c.type = anytype
            elif t == 'blob':
                c.type = str
            elif t == 'real':
                c.type = float
            else:
                status('unknown sqlite type "%s"' % t)

            cols.append(c)
            if r[-1]:
                self.setKeys([c])

        return cols

SqliteSheet.addCommand(ENTER, 'dive-row', 'error("sqlite dbs are readonly")')

def sqlite_type(t):
    if t is int: return 'INTEGER'
    if t in [float, currency]: return 'REAL'
    return 'TEXT'


@asyncthread
def multisave_sqlite(p, *vsheets):
    import sqlite3
    conn = sqlite3.connect(p.resolve())
    c = conn.cursor()

    for vs in vsheets:
        tblname = clean_to_id(vs.name)
        sqlcols = []
        for col in vs.visibleCols:
            sqlcols.append('%s %s' % (col.name, sqlite_type(col.type)))
        sql = 'CREATE TABLE IF NOT EXISTS %s (%s)' % (tblname, ', '.join(sqlcols))
        c.execute(sql)

        for r in Progress(vs.rows, 'saving'):
            sqlvals = []
            for col in vs.visibleCols:
                sqlvals.append(col.getTypedValue(r))
            sql = 'INSERT INTO %s VALUES (%s)' % (tblname, ','.join(['?']*len(sqlvals)))
            c.execute(sql, sqlvals)

    conn.commit()

    status("%s save finished" % p)

save_db = save_sqlite = multisave_db = multisave_sqlite
