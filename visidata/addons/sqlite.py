from visidata import *

def open_sqlite(path):
    vs = SqliteSheet(path.name + '_tables', path, 'sqlite_master')
    vs.columns = vs.getColumns('sqlite_master')
    vs.command(ENTER, 'vd.push(SqliteSheet(joinSheetnames(source.name, cursorRow[1]), sheet, cursorRow[1]))', 'open this table')
    return vs

class SqliteSheet(Sheet):
    """Provide functionality for importing SQLite databases."""
    def __init__(self, name, path_or_sheet, table_name):
        super().__init__(name, path_or_sheet, table_name)
        if isinstance(path_or_sheet, Sheet):
            self.conn = path_or_sheet.conn
        elif isinstance(path_or_sheet, Path):
            import sqlite3
            self.conn = sqlite3.connect(path_or_sheet.resolve())

    def reload(self):
        tblname = self.sources[1]
        self.columns = self.getColumns(tblname)
        r = self.conn.execute('SELECT COUNT(*) FROM %s' % tblname).fetchall()
        self.progressTotal = r[0][0]-1
        self.rows = []
        for i, r in enumerate(self.conn.execute("SELECT * FROM %s" % tblname)):
            self.progressMade = i
            self.rows.append(r)

    def getColumns(self, table_name):
        cols = []
        for i, r in enumerate(self.conn.execute('PRAGMA TABLE_INFO(%s)' % table_name)):
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
