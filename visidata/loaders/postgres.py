from visidata import *

__all__ = ['openurl_postgres', 'openurl_rds', 'PgTable', 'PgTablesSheet']

option('postgres_schema', 'public', 'The desired schema for the Postgres database')

def codeToType(type_code, colname):
    import psycopg2
    try:
        tname = psycopg2._psycopg.string_types[type_code].name
        if 'INTEGER' in tname:
            return int
        if 'STRING' in tname:
            return str
    except KeyError:
        vd.status('unknown postgres type_code %s for %s' % (type_code, colname))
    return anytype


def openurl_rds(url, filetype=None):
    import boto3
    import psycopg2

    rds = boto3.client('rds')
    url = urlparse(url.given)

    _, region, dbname = url.path.split('/')
    token = rds.generate_db_auth_token(url.hostname, url.port, url.username, region)

    conn = psycopg2.connect(
                user=url.username,
                dbname=dbname,
                host=url.hostname,
                port=url.port,
                password=token)

    return PgTablesSheet(dbname+"_tables", sql=SQL(conn))


def openurl_postgres(url, filetype=None):
    import psycopg2

    url = urlparse(url.given)
    dbname = url.path[1:]
    conn = psycopg2.connect(
                user=url.username,
                dbname=dbname,
                host=url.hostname,
                port=url.port,
                password=url.password)

    return PgTablesSheet(dbname+"_tables", sql=SQL(conn))


class SQL:
    def __init__(self, conn):
        self.conn = conn

    def cur(self, qstr):
        import string
        randomname = ''.join(random.choice(string.ascii_uppercase) for _ in range(6))
        cur = self.conn.cursor(randomname)
        cur.execute(qstr)
        return cur

    @asyncthread
    def query_async(self, qstr, callback=None):
        with self.cur(qstr) as cur:
            callback(cur)
            cur.close()


def cursorToColumns(cur, sheet):
    sheet.columns = []
    for i, coldesc in enumerate(cur.description):
        sheet.addColumn(ColumnItem(coldesc.name, i, type=codeToType(coldesc.type_code, coldesc.name)))


# rowdef: (table_name, ncols)
class PgTablesSheet(Sheet):
    rowtype = 'tables'

    def reload(self):
        schema = options.postgres_schema
        qstr = f'''
            SELECT relname table_name, column_count.ncols, reltuples::bigint est_nrows
                FROM pg_class, pg_namespace, (
                    SELECT table_name, COUNT(column_name) AS ncols FROM information_schema.COLUMNS WHERE table_schema = '{schema}' GROUP BY table_name
                    ) AS column_count
                WHERE  pg_class.relnamespace = pg_namespace.oid AND pg_namespace.nspname = '{schema}' AND column_count.table_name = relname;
        '''

        with self.sql.cur(qstr) as cur:
            self.nrowsPerTable = {}

            self.rows = []
            # try to get first row to make cur.description available
            r = cur.fetchone()
            if r:
                self.addRow(r)
            cursorToColumns(cur, self)
            self.setKeys(self.columns[0:1])  # table_name is the key

            for r in cur:
                self.addRow(r)

    def openRow(self, row):
        return PgTable(self.name+"."+row[0], source=row[0], sql=self.sql)


# rowdef: tuple of values as returned by fetchone()
class PgTable(Sheet):
    @asyncthread
    def reload(self):
        with self.sql.cur("SELECT * FROM " + self.source) as cur:
            self.rows = []
            r = cur.fetchone()
            if r:
                self.addRow(r)
            cursorToColumns(cur, self)
            for r in cur:
                self.addRow(r)
