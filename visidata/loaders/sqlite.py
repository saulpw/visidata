from visidata import *

def open_sqlite(path):
    vs = SqliteSheet(path.name + '_tables', path, 'sqlite_master')
    vs.columns = vs.getColumns('sqlite_master')
    vs.command(ENTER, 'vd.push(SqliteSheet(joinSheetnames(source.name, cursorRow[1]), sheet, cursorRow[1]))', 'open this table')
    return vs

class SqliteSheet(Sheet):
    'Provide functionality for importing SQLite databases.'
    def __init__(self, name, pathOrSheet, tableName):
        super().__init__(name, pathOrSheet, tableName)
        if isinstance(pathOrSheet, Sheet):
            self.conn = pathOrSheet.conn
        elif isinstance(pathOrSheet, Path):
            import sqlite3
            self.conn = sqlite3.connect(pathOrSheet.resolve())

    def reload(self):
        tblname = self.sources[1]
        self.columns = self.getColumns(tblname)
        r = self.conn.execute('SELECT COUNT(*) FROM %s' % tblname).fetchall()
        self.rows = []
        for r in self.genProgress(self.conn.execute("SELECT * FROM %s" % tblname), r[0][0]-1):
            self.rows.append(r)

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
                c.width = 0
            elif t == 'real':
                c.type = float
            else:
                status('unknown sqlite type "%s"' % t)
            cols.append(c)
        return cols
