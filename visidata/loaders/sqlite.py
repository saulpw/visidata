from visidata import *

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
                c.type = str
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
