from visidata import ENTER, Sheet, ColumnItem, anytype, status, clean_to_id, Progress, asyncthread, currency, Path, CellColorizer, RowColorizer, vd, options
from visidata import TypedWrapper, TypedExceptionWrapper


def open_sqlite(path):
    vs = SqliteSheet(path.name + '_tables', source=path, tableName='sqlite_master')
    vs.addCommand(ENTER, 'dive-row', 'vd.push(SqliteSheet(joinSheetnames(source.name, cursorRow[1]), source=sheet, tableName=cursorRow[1]))')
    return vs
open_db = open_sqlite3 = open_sqlite


class SqliteSheet(Sheet):
    'Provide functionality for importing SQLite databases.'

    def resolve(self):
        'Resolve all the way back to the original source Path.'
        return self.source.resolve()

    def conn(self):
        import sqlite3
        return sqlite3.connect(self.resolve())

    def execute(self, conn, sql, where={}, parms=None):
        parms = parms or []
        if where:
            sql += ' WHERE %s' % " AND ".join("%s=?" % k for k in where)
        status(sql)
        parms += list(where.values())
        return conn.execute(sql, parms)

    @asyncthread
    def reload(self):
        self.reload_sync()

    def reload_sync(self, _conn=None):
        self.reset()
        with (_conn or self.conn()) as conn:
            tblname = self.tableName
            self.columns = self.getColumns(tblname, conn)
            self.recalc()
            r = self.execute(conn, 'SELECT COUNT(*) FROM %s' % tblname).fetchall()
            rowcount = r[0][0]
            self.rows = []
            for row in Progress(self.execute(conn, "SELECT * FROM %s" % tblname), total=rowcount-1):
                self.addRow(row)

    def save(self):
        adds, changes, deletes = self.getDeferredChanges()
        options_safe_error = options.safe_error
        def value(row, col):
            v = col.getTypedValue(row)
            if isinstance(v, TypedWrapper):
                if isinstance(v, TypedExceptionWrapper):
                    return options_safe_error
                else:
                    return None
            return v

        def values(row, cols):
            vals = []
            for c in cols:
                vals.append(value(row, c))
            return vals

        with self.conn() as conn:
            wherecols = self.keyCols or self.visibleCols
            for r in adds.values():
                cols = self.visibleCols
                sql = 'INSERT INTO %s ' % self.tableName
                sql += '(%s)' % ','.join(c.name for c in cols)
                sql += 'VALUES (%s)' % ','.join('?' for c in cols)
                self.execute(conn, sql, parms=values(r, cols))

            for r, changedcols in changes.values():
                sql = 'UPDATE %s SET ' % self.tableName
                sql += ', '.join('%s=?' % c.name for c in changedcols)
                self.execute(conn, sql,
                            where={c.name: c.getSavedValue(r) for c in wherecols},
                            parms=values(r, changedcols))

            for r in deletes.values():
                self.execute(conn, 'DELETE FROM %s ' % self.tableName,
                              where={c.name: c.getTypedValue(r) for c in wherecols})

            conn.commit()

    def getColumns(self, tableName, conn):
        cols = []
        for i, r in enumerate(self.execute(conn, 'PRAGMA TABLE_INFO(%s)' % tableName)):
            c = Column(r[1], getter=lambda col,row,idx=i: row[idx])
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
