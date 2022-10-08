import re

from visidata import VisiData, vd, Sheet, options, Column, Progress, anytype, date, ColumnItem, asyncthread, TypedExceptionWrapper, TypedWrapper, IndexSheet, copy, currency, clean_to_id


@VisiData.api
def open_sqlite(vd, p):
    return SqliteIndexSheet(p.name, source=p)

@VisiData.api
def openurl_sqlite(vd, p, filetype=None):
    return SqliteIndexSheet(p.name, source=p)

VisiData.open_sqlite3 = VisiData.open_sqlite
VisiData.open_db = VisiData.open_sqlite

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
        con = sqlite3.connect(str(self.resolve()))
        con.text_factory = lambda s, enc=self.options.encoding, encerrs=self.options.encoding_errors: s.decode(enc, encerrs)
        return con

    def execute(self, conn, sql, parms=None):
        parms = parms or []
        vd.debug(sql)
        return conn.execute(sql, parms)

    def iterload(self):
        import sqlite3

        def parse_sqlite_type(t):
            m = re.match(r'(\w+)(\((\d+)(,(\d+))?\))?', t.upper())
            if not m: return anytype
            typename, _, i, _, f = m.groups()
            if typename == 'DATE': return date
            if typename == 'INTEGER': return int
            if typename == 'REAL': return float
            if typename == 'NUMBER':
                return int if f == '0' else float
            return anytype

        self.rowidColumn = None
        with self.conn() as conn:
            tblname = self.tableName
            if not isinstance(self, SqliteIndexSheet):
                self.columns = []
                for r in self.execute(conn, 'PRAGMA TABLE_XINFO("%s")' % tblname):
                    colnum, colname, coltype, nullable, defvalue, colkey, *_ = r
                    c = ColumnItem(colname, colnum+1, type=parse_sqlite_type(coltype))
                    self.addColumn(c)

                    if colkey:
                        self.setKeys([c])

                sql = self.row[5]  # SQL used to create table
                if 'WITHOUT ROWID' not in sql and 'CREATE VIEW' not in sql:
                    self.rowidColumn = ColumnItem('rowid', 0, type=int, width=0)
                    self.addColumn(self.rowidColumn, index=0)

            if self.rowidColumn:
                r = self.execute(conn, 'SELECT rowid, * FROM "%s"' % tblname)
            else:
                r = self.execute(conn, 'SELECT NULL, * FROM "%s"' % tblname)
            yield from Progress(r, total=r.rowcount-1)

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
            for r in adds.values():
                cols = self.visibleCols
                sql = 'INSERT INTO "%s" ' % self.tableName
                sql += '(%s)' % ','.join(c.name for c in cols)
                sql += ' VALUES (%s)' % ','.join('?' for c in cols)
                res = self.execute(conn, sql, parms=values(r, cols))
                if res.rowcount != res.arraysize:
                    vd.warning('not all rows inserted') # f'{res.rowcount}/{res.arraysize} rows inserted'

            for row, rowmods in mods.values():
                if not self.rowidColumn:
                    vd.warning('cannot modify rows in tables without rowid')
                    break
                wherecols = [self.rowidColumn]
                sql = 'UPDATE "%s" SET ' % self.tableName
                sql += ', '.join('%s=?' % c.name for c, _ in rowmods.items())
                sql += ' WHERE %s' % ' AND '.join('"%s"=?' % c.name for c in wherecols)
                newvals=values(row, [c for c, _ in rowmods.items()])
                # calcValue gets the 'previous' value (before update)
                wherevals=list(Column.calcValue(c, row) or '' for c in wherecols)
                res = self.execute(conn, sql, parms=newvals+wherevals)
                if res.rowcount != res.arraysize:
                    vd.warning('not all rows updated') # f'{res.rowcount}/{res.arraysize} rows updated'

            for row in dels.values():
                if not self.rowidColumn:
                    vd.warning('cannot delete rows in tables without rowid')
                    break

                wherecols = [self.rowidColumn]
                sql = 'DELETE FROM "%s" ' % self.tableName
                sql += ' WHERE %s' % ' AND '.join('"%s"=?' % c.name for c in wherecols)
                wherevals=list(Column.calcValue(c, row) for c in wherecols)
                res = self.execute(conn, sql, parms=wherevals)
                if res.rowcount != res.arraysize:
                    vd.warning('not all rows deleted') # f'{res.rowcount}/{res.arraysize} rows deleted'

            conn.commit()

        self.preloadHook()
        self.reload()


class SqliteIndexSheet(SqliteSheet, IndexSheet):
    rowtype = 'tables'
    tableName = 'sqlite_master'
    savesToSource = True
    defer = True
    def iterload(self):
        self.addColumn(Column('sql', width=0, getter=lambda c,r:r.row[5]))
        for row in SqliteSheet.iterload(self):
            if row[1] != 'index':
                tblname = row[2]
                yield SqliteSheet(tblname, source=self, tableName=tblname, row=row)

    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()
        with self.conn() as conn:
            for r in adds.values():
                vd.warning('create a new table by saving a new sheet to this database file')

            for row, rowmods in mods.values():
                cname = self.column('name')
                if len(rowmods) == 1 and cname in rowmods:
                    sql='ALTER TABLE "%s" RENAME TO "%s"' % (cname.calcValue(row), rowmods[cname])
                    self.execute(conn, sql)
                else:
                    vd.warning('can only modify table name')

            for row in dels.values():
                sql = 'DROP TABLE "%s"' % row.tableName
                self.execute(conn, sql)

            conn.commit()

        self.preloadHook()
        self.reload()

class SqliteQuerySheet(SqliteSheet):
    def iterload(self):
        with self.conn() as conn:
            self.columns = []
            for c in type(self).columns:
                self.addColumn(copy(c))
            self.result = self.execute(conn, self.query, parms=getattr(self, 'parms', []))
            for i, desc in enumerate(self.result.description):
                self.addColumn(ColumnItem(desc[0], i))

            for row in self.result:
                yield row



@VisiData.api
def save_sqlite(vd, p, *vsheets):
    import sqlite3
    conn = sqlite3.connect(str(p))
    conn.text_factory = lambda s, enc=vsheets[0].options.encoding: s.decode(enc)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    sqltypes = {
        int: 'INTEGER',
        float: 'REAL',
        currency: 'REAL'
    }

    for vs in vsheets:
        vs.ensureLoaded()
    vd.sync()

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
            sql = 'INSERT INTO "%s" (%s) VALUES (%s)' % (tblname, ','.join(f'"{c.name}"' for c in vs.visibleCols), ','.join('?' for v in sqlvals))
            c.execute(sql, sqlvals)

    conn.commit()

    vd.status("%s save finished" % p)


SqliteIndexSheet.addCommand('a', 'add-table', 'fail("create a new table by saving a sheet to this database file")', 'stub; add table by saving a sheet to the db file instead')
SqliteIndexSheet.bindkey('ga', 'add-table')
SqliteSheet.options.header = 0
VisiData.save_db = VisiData.save_sqlite

vd.addGlobals({
    'SqliteIndexSheet': SqliteIndexSheet,
    'SqliteSheet': SqliteSheet,
    'SqliteQuerySheet': SqliteQuerySheet
})
