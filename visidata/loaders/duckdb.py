import json

from visidata import vd, VisiData, Sheet, Column, Progress, anytype, ItemColumn, asyncthread, TypedExceptionWrapper, TypedWrapper, IndexSheet, AttrColumn, vlen
from visidata.type_date import date


vd.option('duckdb_onconnect', '', 'duckdb statement to execute after opening a connection')


def _quote_ident(name):
    return '"' + str(name).replace('"', '""') + '"'


def _quote_literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def _relation_arg(sheet):
    parts = [sheet.schema_name, sheet.table_name]
    return '.'.join(part for part in parts if part)


def _relation_ref(sheet):
    parts = [sheet.schema_name, sheet.table_name]
    return '.'.join(_quote_ident(part) for part in parts if part)


def _parse_duckdb_type(dtype):
    typename = str(dtype).upper()

    if typename == 'BOOLEAN':
        return bool
    if any(tok in typename for tok in ('HUGEINT', 'BIGINT', 'INTEGER', 'SMALLINT', 'TINYINT', 'UBIGINT', 'UINTEGER', 'USMALLINT', 'UTINYINT', 'INT2', 'INT4', 'INT8')):
        return int
    if any(tok in typename for tok in ('DOUBLE', 'FLOAT', 'REAL', 'DECIMAL', 'NUMERIC')):
        return float
    if any(tok in typename for tok in ('TIMESTAMP', 'DATE', 'TIME')):
        return date
    if any(tok in typename for tok in ('VARCHAR', 'TEXT', 'CHAR', 'STRING', 'UUID')):
        return str

    return anytype


def _iterfetch(result, batch_size=1000):
    while True:
        rows = result.fetchmany(batch_size)
        if not rows:
            break
        yield from rows


@VisiData.api
def guess_duckdb(vd, p):
    if p.open_bytes().read(12)[8:12] == b'DUCK':
        return dict(filetype='duckdb', _likelihood=10)


@VisiData.api
def open_duckdb(vd, p):
    if not p.is_local():
        vd.fail('duckdb requires an uncompressed, local file')
    return DuckdbIndexSheet(p.base_stem, source=p)


# rowdef: list of values
class DuckdbSheet(Sheet):
    'Provide functionality for importing DuckDB databases.'
    rowtype = 'rows'
    savesToSource = True
    defer = True
    query = ''
    table_name = ''
    table_type = ''
    schema_name = 'main'
    database_name = ''
    create_sql = ''

    def conn(self, read_only=True):
        duckdb = vd.importExternal('duckdb')
        localpath = self.rootSheet().source
        con = duckdb.connect(str(localpath), read_only=read_only)
        if self.options.duckdb_onconnect:
            con.execute(self.options.duckdb_onconnect)
        return con

    def rawSql(self, qstr):
        return DuckdbSheet('query', source=self.source, query=qstr)

    @property
    def sidebar(self):
        if self.query:
            return '# SQL\n' + self.query
        return super().sidebar

    def execute(self, conn, sql, parms=None):
        vd.debug(sql)
        if parms is None:
            return conn.execute(sql)
        return conn.execute(sql, parms)

    def iterload_table(self):
        self.pk_columns = []

        conn = self.conn()
        try:
            if not isinstance(self, DuckdbIndexSheet):
                self.columns = []
                pragma_sql = f'CALL pragma_table_info({_quote_literal(_relation_arg(self))})'
                for i, row in enumerate(self.execute(conn, pragma_sql).fetchall()):
                    _, colname, coltype, *_rest, colkey = row
                    c = ItemColumn(colname, i, type=_parse_duckdb_type(coltype))
                    self.addColumn(c)
                    if colkey:
                        self.pk_columns.append(c)

                if self.pk_columns:
                    self.setKeys(self.pk_columns)

            result = self.execute(conn, f'SELECT * FROM {_relation_ref(self)}')
            yield from _iterfetch(result)
        finally:
            conn.close()

    def iterload_query(self, query):
        conn = self.conn()
        try:
            self.columns = []
            result = self.execute(conn, query, parms=getattr(self, 'parms', None))
            for i, desc in enumerate(result.description):
                self.addColumn(ItemColumn(desc[0], i, type=_parse_duckdb_type(desc[1])))

            yield from _iterfetch(result)
        finally:
            conn.close()

    def iterload(self):
        if self.table_name:
            yield from self.iterload_table()
        elif self.query:
            yield from self.iterload_query(self.query)
        else:
            vd.fail('no query or tablename to load')

    @asyncthread
    def putChanges(self):
        if not self.table_name:
            vd.fail('cannot commit query results')

        adds, mods, dels = self.getDeferredChanges()

        def value(row, col):
            v = col.getTypedValue(row)
            if isinstance(v, TypedWrapper):
                if isinstance(v, TypedExceptionWrapper):
                    return self.options.safe_error
                return None
            if not isinstance(v, (int, float, str, bool)):
                v = col.getFullDisplayValue(row)
            return v

        def values(row, cols):
            return [value(row, c) for c in cols]

        conn = self.conn(read_only=False)
        try:
            conn.begin()

            for row in adds.values():
                cols = self.visibleCols
                sql = f'INSERT INTO {_relation_ref(self)} ({",".join(_quote_ident(c.name) for c in cols)}) VALUES ({",".join("?" for _ in cols)})'
                self.execute(conn, sql, parms=values(row, cols))

            wherecols = list(getattr(self, 'pk_columns', []))

            for row, rowmods in mods.values():
                if not wherecols:
                    vd.warning('cannot modify rows in tables without primary key')
                    break

                sql = f'UPDATE {_relation_ref(self)} SET '
                sql += ', '.join(f'{_quote_ident(c.name)}=?' for c in rowmods)
                sql += ' WHERE ' + ' AND '.join(f'{_quote_ident(c.name)}=?' for c in wherecols)
                newvals = values(row, list(rowmods))
                wherevals = [Column.calcValue(c, row) for c in wherecols]
                self.execute(conn, sql, parms=newvals + wherevals)

            for row in dels.values():
                if not wherecols:
                    vd.warning('cannot delete rows in tables without primary key')
                    break

                sql = f'DELETE FROM {_relation_ref(self)} WHERE '
                sql += ' AND '.join(f'{_quote_ident(c.name)}=?' for c in wherecols)
                wherevals = [Column.calcValue(c, row) for c in wherecols]
                self.execute(conn, sql, parms=wherevals)

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self.preloadHook()
        self.reload()

# rowdef: DuckdbSheet for one table or view in the database
class DuckdbIndexSheet(DuckdbSheet, IndexSheet):
    rowtype = 'tables'
    savesToSource = True
    defer = True

    def iterload(self):
        conn = self.conn()
        try:
            metadata_sql = '''
                SELECT
                    table_name AS relation_name,
                    schema_name,
                    database_name,
                    'BASE TABLE' AS relation_type,
                    sql
                FROM duckdb_tables()
                WHERE NOT internal AND NOT temporary
            UNION ALL
                SELECT
                    view_name AS relation_name,
                    schema_name,
                    database_name,
                    'VIEW' AS relation_type,
                    sql
                FROM duckdb_views()
                WHERE NOT internal AND NOT temporary
                ORDER BY schema_name, relation_name, relation_type
            '''

            for relation_name, schema_name, database_name, relation_type, sql in self.execute(conn, metadata_sql).fetchall():
                yield DuckdbSheet(
                    relation_name,
                    source=self,
                    table_name=relation_name,
                    schema_name=schema_name,
                    database_name=database_name,
                    table_type=relation_type,
                    create_sql=sql,
                )
        finally:
            conn.close()

    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()
        name_col = self.column('name')

        conn = self.conn(read_only=False)
        try:
            conn.begin()

            for row in adds.values():
                vd.warning('create a new table by saving a sheet to this database file')

            for row, rowmods in mods.values():
                if len(rowmods) == 1 and name_col in rowmods:
                    relation_kind = 'VIEW' if row.table_type == 'VIEW' else 'TABLE'
                    sql = f'ALTER {relation_kind} {_relation_ref(row)} RENAME TO {_quote_ident(rowmods[name_col])}'
                    self.execute(conn, sql)
                else:
                    vd.warning('can only modify table or view name')

            for row in dels.values():
                relation_kind = 'VIEW' if row.table_type == 'VIEW' else 'TABLE'
                self.execute(conn, f'DROP {relation_kind} {_relation_ref(row)}')

            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

        self.preloadHook()
        self.reload()


DuckdbIndexSheet.columns = IndexSheet.columns[:1] + [
    AttrColumn('schema_name'),
    AttrColumn('table_type'),
    AttrColumn('database_name', width=0),
] + IndexSheet.columns[1:] + [
    Column('sql', width=0, getter=lambda c, r: r.create_sql or ''),
]


@VisiData.api
def save_duckdb(vd, p, *vsheets):
    duckdb = vd.importExternal('duckdb')
    jsonenc = json.JSONEncoder()

    conn = duckdb.connect(str(p))
    sqltypes = {
        bool: 'BOOLEAN',
        int: 'BIGINT',
        vlen: 'BIGINT',
        float: 'DOUBLE',
        date: 'DATE',
        str: 'VARCHAR',
    }

    for t in vd.numericTypes:
        if t not in sqltypes:
            sqltypes[t] = 'DOUBLE'

    for vs in vsheets:
        vs.ensureLoaded()
    vd.sync()

    try:
        conn.begin()
        for vs in vsheets:
            tblname = vd.cleanName(vs.name)
            sqlcols = [f'{_quote_ident(col.name)} {sqltypes.get(col.type, "VARCHAR")}' for col in vs.visibleCols]
            conn.execute(f'CREATE TABLE IF NOT EXISTS {_quote_ident(tblname)} ({", ".join(sqlcols)})')

            for row in Progress(vs.rows, 'saving'):
                sqlvals = []
                for col in vs.visibleCols:
                    value = col.getTypedValue(row)
                    if isinstance(value, TypedWrapper):
                        if isinstance(value, TypedExceptionWrapper):
                            value = vs.options.safe_error
                        else:
                            value = None
                    elif isinstance(value, (list, tuple, dict)):
                        value = jsonenc.encode(value)
                    elif not isinstance(value, (int, float, str, bool)):
                        value = col.getFullDisplayValue(row)
                    sqlvals.append(value)

                placeholders = ','.join('?' for _ in sqlvals)
                columns = ','.join(_quote_ident(c.name) for c in vs.visibleCols)
                conn.execute(f'INSERT INTO {_quote_ident(tblname)} ({columns}) VALUES ({placeholders})', sqlvals)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


DuckdbSheet.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')
DuckdbIndexSheet.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')
DuckdbIndexSheet.addCommand('a', 'add-table', 'fail("create a new table by saving a sheet to this database file")', 'stub; add table by saving a sheet to the db file instead')
DuckdbIndexSheet.bindkey('ga', 'add-table')
DuckdbSheet.options.header = 0

VisiData.open_ddb = VisiData.open_duckdb
VisiData.save_ddb = VisiData.save_duckdb

vd.addGlobals(DuckdbIndexSheet=DuckdbIndexSheet, DuckdbSheet=DuckdbSheet)
