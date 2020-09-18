from visidata import *

def open_sqlite(p):
    return SqliteIndexSheet(p.name, source=p)

open_sqlite3 = open_sqlite
open_db = open_sqlite

# rowdef: list of values
class SqliteSheet(Sheet):
    'Provide functionality for importing SQLite databases.'
    savesToSource = True
    defer = True

    def resolve(self):
        'Resolve all the way back to the original source Path.'
        return self.source.resolve()

    def conn(self):
        import sqlite3
        return sqlite3.connect(str(self.resolve()))

    def execute(self, conn, sql, parms=None):
        parms = parms or []
        vd.status(sql)
        return conn.execute(sql, parms)

    def iterload(self):
        sqltypes = {
            'INTEGER': int,
            'TEXT': anytype,
            'BLOB': str,
            'REAL': float
        }

        with self.conn() as conn:
            tblname = self.tableName
            if not isinstance(self, SqliteIndexSheet):
                self.columns = []
                for i, r in enumerate(self.execute(conn, 'PRAGMA TABLE_INFO("%s")' % tblname)):
                    c = ColumnItem(r[1], i, type=sqltypes.get(r[2].upper(), anytype))
                    self.addColumn(c)

                    if r[-1]:
                        self.setKeys([c])

            r = self.execute(conn, 'SELECT COUNT(*) FROM "%s"' % tblname).fetchall()
            rowcount = r[0][0]
            for row in Progress(self.execute(conn, 'SELECT * FROM "%s"' % tblname), total=rowcount-1):
                yield list(row)

    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()
        options_safe_error = options.safe_error
        def value(row, col):
            v = col.getTypedValue(row)
            if isinstance(v, TypedWrapper):
                if isinstance(v, TypedExceptionWrapper):
                    return options_safe_error
                else:
                    return None
            elif not isinstance(v, (int, float, str)):
                v = col.getDisplayValue(r)
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
                sql = 'INSERT INTO "%s" ' % self.tableName
                sql += '(%s)' % ','.join(c.name for c in cols)
                sql += 'VALUES (%s)' % ','.join('?' for c in cols)
                self.execute(conn, sql, parms=values(r, cols))

            for row, rowmods in mods.values():
                sql = 'UPDATE "%s" SET ' % self.tableName
                sql += ', '.join('%s=?' % c.name for c, _ in rowmods.items())
                sql += ' WHERE %s' % ' AND '.join('"%s"=?' % c.name for c in wherecols)
                self.execute(conn, sql,
                            parms=values(row, [c for c, _ in rowmods.items()]) + list(c.getSavedValue(row) for c in wherecols))

            for r in dels.values():
                sql = 'DELETE FROM "%s" ' % self.tableName
                sql += ' WHERE %s' % ' AND '.join('"%s"=?' % c.name for c in wherecols)
                self.execute(conn, sql, parms=list(c.getTypedValue(r) for c in wherecols))

            conn.commit()

        self.preloadHook()
        self.reload()


class SqliteIndexSheet(SqliteSheet, IndexSheet):
    tableName = 'sqlite_master'
    def iterload(self):
        for row in SqliteSheet.iterload(self):
            if row[0] != 'index':
                tblname = row[1]
                yield SqliteSheet(tblname, source=self, tableName=tblname, row=row)


class SqliteQuerySheet(SqliteSheet):
    def iterload(self):
        with self.conn() as conn:
            self.columns = []

            self.result = self.execute(conn, self.query, parms=getattr(self, 'parms', []))
            for i, desc in enumerate(self.result.description):
                self.addColumn(ColumnItem(desc[0], i))

            for row in self.result:
                yield row



@VisiData.api
def save_sqlite(vd, p, *vsheets):
    import sqlite3
    conn = sqlite3.connect(str(p))
    c = conn.cursor()

    sqltypes = {
        int: 'INTEGER',
        float: 'REAL',
        currency: 'REAL'
    }

    for vs in vsheets:
        tblname = clean_to_id(vs.name)
        sqlcols = []
        for col in vs.visibleCols:
            sqlcols.append('"%s" %s' % (col.name, sqltypes.get(col.type, 'TEXT')))
        sql = 'CREATE TABLE IF NOT EXISTS "%s" (%s)' % (tblname, ', '.join(sqlcols))
        c.execute(sql)

        for r in Progress(vs.rows, 'saving'):
            sqlvals = []
            for col in vs.visibleCols:
                v = col.getTypedValue(r)
                if isinstance(v, TypedWrapper):
                    if isinstance(v, TypedExceptionWrapper):
                        v = options.safe_error
                    else:
                        v = None
                elif not isinstance(v, (int, float, str)):
                    v = col.getDisplayValue(r)
                sqlvals.append(v)
            sql = 'INSERT INTO "%s" VALUES (%s)' % (tblname, ','.join('?' for v in sqlvals))
            c.execute(sql, sqlvals)

    conn.commit()

    vd.status("%s save finished" % p)


SqliteSheet.class_options.header = 0
VisiData.save_db = VisiData.save_sqlite
