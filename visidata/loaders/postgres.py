import random
import string
from contextlib import contextmanager
from urllib.parse import urlparse, unquote

from visidata import VisiData, vd, Sheet, IndexSheet, Column, options, anytype, asyncthread, ColumnItem, TypedExceptionWrapper, TypedWrapper

__all__ = ['openurl_postgres', 'openurl_rds', 'PgTable', 'PgTablesSheet']

vd.option('postgres_schema', 'public', 'The desired schema for the Postgres database')
vd.option('postgres_user', '', 'postgres username (overrides URL)')
vd.option('postgres_password', '', 'postgres password (overrides URL)')
vd.option('postgres_host', '', 'postgres hostname (overrides URL)')
vd.option('postgres_port', 0, 'postgres port (overrides URL)')


def codeToType(type_code, colname):
    psycopg2 = vd.importExternal('psycopg2', 'psycopg2-binary')
    try:
        tname = psycopg2._psycopg.string_types[type_code].name
        if 'INTEGER' in tname:
            return int
        if 'STRING' in tname:
            return str
    except KeyError:
        vd.status('unknown postgres type_code %s for %s' % (type_code, colname))
    return anytype


class SQL:
    def __init__(self, url, rds=False):
        self.url = url
        self.rds = rds

    def _connect(self):
        psycopg2 = vd.importExternal('psycopg2', 'psycopg2-binary')

        url = self.url
        if self.rds:
            boto3 = vd.importExternal('boto3')
            rds = boto3.client('rds')
            password = rds.generate_db_auth_token(url.hostname, url.port, url.username, self._rds_region)
        else:
            password = vd.options.postgres_password or (unquote(url.password) if url.password else None)

        kwargs = dict(dbname=self.dbname)
        u = vd.options.postgres_user or url.username
        h = vd.options.postgres_host or url.hostname
        p = vd.options.postgres_port or url.port
        if u: kwargs['user'] = u
        if h: kwargs['host'] = h
        if p: kwargs['port'] = p
        if password: kwargs['password'] = password

        return psycopg2.connect(**kwargs)

    @contextmanager
    def cur(self, qstr):
        conn = self._connect()
        randomname = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        cur = conn.cursor(randomname, withhold=True)
        try:
            cur.execute(qstr)
            conn.commit()
            yield cur
        finally:
            cur.close()
            conn.close()

    @contextmanager
    def conn(self):
        conn = self._connect()
        try:
            yield conn
        finally:
            conn.close()


@VisiData.api
def openurl_rds(vd, url, filetype=None):
    url = urlparse(url.given)
    parts = url.path.strip('/').split('/')
    region = parts[0]
    dbname = parts[1] if len(parts) > 1 else ''
    tablename = parts[2] if len(parts) > 2 else None

    sql = SQL(url, rds=True)
    sql._rds_region = region
    sql.dbname = dbname

    if tablename:
        return PgTable(dbname+"."+tablename, source=tablename, sql=sql)
    return PgTablesSheet(dbname+"_tables", sql=sql)


@VisiData.api
def openurl_postgres(vd, url, filetype=None):
    url = urlparse(url.given)
    parts = url.path.strip('/').split('/')
    dbname = parts[0]
    tablename = parts[1] if len(parts) > 1 else None

    sql = SQL(url)
    sql.dbname = dbname

    if tablename:
        return PgTable(dbname+"."+tablename, source=tablename, sql=sql)
    return PgTablesSheet(dbname+"_tables", sql=sql)


VisiData.openurl_postgresql = VisiData.openurl_postgres


@VisiData.api
def postgresGetColumns(vd, cur):
    for i, coldesc in enumerate(cur.description):
        yield ColumnItem(coldesc.name, i, type=codeToType(coldesc.type_code, coldesc.name))


# rowdef: PgTable sheet
class PgTablesSheet(IndexSheet):
    rowtype = 'tables'

    def iterload(self):
        schema = options.postgres_schema
        qstr = f'''
            SELECT relname table_name, column_count.ncols, reltuples::bigint est_nrows
                FROM pg_class, pg_namespace, (
                    SELECT table_name, COUNT(column_name) AS ncols FROM information_schema.COLUMNS WHERE table_schema = '{schema}' GROUP BY table_name
                    ) AS column_count
                WHERE  pg_class.relnamespace = pg_namespace.oid AND pg_namespace.nspname = '{schema}' AND column_count.table_name = relname;
        '''

        with self.sql.cur(qstr) as cur:
            r = cur.fetchone()
            if r:
                yield PgTable(r[0], source=r[0], sql=self.sql)
            for r in cur:
                yield PgTable(r[0], source=r[0], sql=self.sql)

    def rawSql(self, q):
        return PgQuerySheet(q[:40], sql=self.sql, query=q)


# rowdef: list of values
class PgTable(Sheet):
    savesToSource = True
    defer = True
    query = ''
    tableName = ''

    @property
    def sidebar(self):
        if self.query:
            return '# SQL\n' + self.query
        return super().sidebar

    def iterload(self):
        if self.query:
            yield from self.iterload_query(self.query)
        else:
            yield from self.iterload_table(self.source)

    def iterload_table(self, tblname):
        if self.options.postgres_schema:
            source = f'"{self.options.postgres_schema}"."{tblname}"'
        else:
            source = f'"{tblname}"'

        # get primary keys for this table  #579
        self._pkeyNames = []
        try:
            schema = self.options.postgres_schema or 'public'
            pkqstr = f'''SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = '{schema}'
                    AND tc.table_name = '{tblname}'
                    AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position'''
            with self.sql.cur(pkqstr) as pkcur:
                self._pkeyNames = [r[0] for r in pkcur]
        except Exception:
            pass

        self.tableName = tblname
        with self.sql.cur(f"SELECT * FROM {source}") as cur:
            self.columns = []
            r = cur.fetchone()
            if r:
                for c in vd.postgresGetColumns(cur):
                    self.addColumn(c)
                yield list(r)
            else:
                for c in vd.postgresGetColumns(cur):
                    self.addColumn(c)

            # set key columns based on primary keys
            self._pkeyColumns = []
            for pkname in self._pkeyNames:
                for c in self.columns:
                    if c.name == pkname:
                        self._pkeyColumns.append(c)
                        self.setKeys([c])

            for r in cur:
                yield list(r)

    def iterload_query(self, query):
        with self.sql.cur(query) as cur:
            self.columns = []
            r = cur.fetchone()
            if r:
                for c in vd.postgresGetColumns(cur):
                    self.addColumn(c)
                yield list(r)
            else:
                for c in vd.postgresGetColumns(cur):
                    self.addColumn(c)
            for r in cur:
                yield list(r)

    def rawSql(self, q):
        return PgQuerySheet(q[:40], sql=self.sql, query=q)

    def rowid(self, row):
        if getattr(self, '_pkeyColumns', None):
            return tuple(c.calcValue(row) for c in self._pkeyColumns)
        return id(row)

    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()

        def value(row, col):
            v = col.getTypedValue(row)
            if isinstance(v, TypedWrapper):
                if isinstance(v, TypedExceptionWrapper):
                    return options.safe_error
                else:
                    return None
            elif not isinstance(v, (int, float, str)):
                v = col.getDisplayValue(row)
            return v

        def values(row, cols):
            return [value(row, c) for c in cols]

        with self.sql.conn() as conn:
            cur = conn.cursor()

            for r in adds.values():
                cols = self.visibleCols
                sql = 'INSERT INTO "%s" ' % self.tableName
                sql += '(%s)' % ','.join('"%s"' % c.name for c in cols)
                sql += ' VALUES (%s)' % ','.join('%s' for c in cols)
                cur.execute(sql, values(r, cols))

            for row, rowmods in mods.values():
                if not getattr(self, '_pkeyColumns', None):
                    vd.warning('cannot modify rows in tables without primary key')
                    break
                sql = 'UPDATE "%s" SET ' % self.tableName
                sql += ', '.join('"%s"=%%s' % c.name for c, _ in rowmods.items())
                sql += ' WHERE %s' % ' AND '.join('"%s"=%%s' % c.name for c in self._pkeyColumns)
                newvals = values(row, [c for c, _ in rowmods.items()])
                wherevals = [Column.calcValue(c, row) for c in self._pkeyColumns]
                cur.execute(sql, newvals + wherevals)

            for row in dels.values():
                if not getattr(self, '_pkeyColumns', None):
                    vd.warning('cannot delete rows in tables without primary key')
                    break
                sql = 'DELETE FROM "%s" ' % self.tableName
                sql += ' WHERE %s' % ' AND '.join('"%s"=%%s' % c.name for c in self._pkeyColumns)
                wherevals = [Column.calcValue(c, row) for c in self._pkeyColumns]
                cur.execute(sql, wherevals)

            conn.commit()
            cur.close()

        self.preloadHook()
        self.reload()


class PgQuerySheet(PgTable):
    'Sheet for results of a raw SQL query.'
    savesToSource = False
    defer = False

    def iterload(self):
        yield from self.iterload_query(self.query)


PgTable.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')
PgTable.addCommand('', 'edit-sql', 'vd.push(rawSql(input("edit SQL: ", value=query, type="sql")))', 'edit and re-execute SQL query')
PgTablesSheet.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')

vd.addGlobals(PgTablesSheet=PgTablesSheet, PgTable=PgTable)
