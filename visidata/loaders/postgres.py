import random
import string
from contextlib import contextmanager
from urllib.parse import urlparse, unquote

from visidata import VisiData, vd, Sheet, IndexSheet, anytype, ItemColumn, UNLOADED

__all__ = ['openurl_postgres', 'openurl_postgresql', 'openurl_rds', 'PgTable', 'PgTablesSheet']

vd.option('postgres_schema', 'public', 'desired schema for the Postgres database')


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
            password = unquote(url.password) if url.password else None

        kwargs = dict(dbname=self.dbname)
        if url.username: kwargs['user'] = url.username
        if url.hostname: kwargs['host'] = url.hostname
        if url.port: kwargs['port'] = url.port
        if password: kwargs['password'] = password

        return psycopg2.connect(**kwargs)

    @contextmanager
    def cur(self, qstr, params=None):
        conn = self._connect()
        randomname = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        try:
            cur = conn.cursor(randomname)
            cur.execute(qstr, params)
            yield cur
            cur.close()
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


openurl_postgresql = openurl_postgres
VisiData.openurl_postgresql = VisiData.openurl_postgres


class PgColumn(ItemColumn):
    @property
    def readonly(self):
        return True  #579


@VisiData.api
def postgresGetColumns(vd, cur):
    for i, coldesc in enumerate(cur.description):
        yield PgColumn(coldesc.name, i, type=codeToType(coldesc.type_code, coldesc.name))


# rowdef: PgTable sheet
class PgTablesSheet(IndexSheet):
    rowtype = 'tables'

    def iterload(self):
        qstr = '''
            SELECT relname table_name, column_count.ncols, reltuples::bigint est_nrows
                FROM pg_class, pg_namespace, (
                    SELECT table_name, COUNT(column_name) AS ncols FROM information_schema.COLUMNS WHERE table_schema = %(schema)s GROUP BY table_name
                    ) AS column_count
                WHERE  pg_class.relnamespace = pg_namespace.oid AND pg_namespace.nspname = %(schema)s AND column_count.table_name = relname;
        '''

        with self.sql.cur(qstr, dict(schema=self.options.postgres_schema)) as cur:
            for tblname, ncols, est_nrows in cur:
                yield PgTable(tblname, source=tblname, sql=self.sql,
                              column_count=ncols,
                              estimated_rows=est_nrows if est_nrows >= 0 else None)

    def rawSql(self, q):
        return PgQuerySheet(q[:40], sql=self.sql, query=q)


# rowdef: list of values
class PgTable(Sheet):
    defer = True
    query = ''
    estimated_rows = None
    column_count = None

    @property
    def nRows(self):
        if self.rows is UNLOADED and self.estimated_rows is not None:
            return self.estimated_rows
        return super().nRows

    @property
    def nCols(self):
        if self.rows is UNLOADED and self.column_count is not None:
            return self.column_count
        return super().nCols

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
        vd.importExternal('psycopg2', 'psycopg2-binary')
        from psycopg2 import sql
        if self.options.postgres_schema:
            source = sql.Identifier(self.options.postgres_schema, tblname)
        else:
            source = sql.Identifier(tblname)

        with self.sql.cur(sql.SQL("SELECT * FROM {}").format(source)) as cur:
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

    def commit(self, *rows):
        vd.fail('saving changes to postgres is not supported yet')  #579


class PgQuerySheet(PgTable):
    'Sheet for results of a raw SQL query.'
    def iterload(self):
        yield from self.iterload_query(self.query)


PgTable.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')
PgTable.addCommand('', 'edit-sql', 'vd.push(rawSql(input("edit SQL: ", value=query, type="sql")))', 'edit and re-execute SQL query')
PgTablesSheet.addCommand('', 'exec-sql', 'vd.push(rawSql(input("execute SQL: ", type="sql")))', 'execute raw SQL statement')

PgTablesSheet.class_options.load_lazy = True  #282

vd.addGlobals(PgTablesSheet=PgTablesSheet, PgTable=PgTable)
