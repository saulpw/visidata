from visidata import *

__all__ = ['openurl_mysql', 'MyTable', 'MyTablesSheet']

def codeToType(type_code, colname):
    import MySQLdb as mysql

    types = mysql.constants.FIELD_TYPE

    if type_code in (types.TINY, types.SHORT, types.LONG, types.LONGLONG, types.INT24,):
        return int

    if type_code in (types.FLOAT, types.DOUBLE, types.DECIMAL, types.NEWDECIMAL,):
        return float

    if type_code == mysql.STRING:
        return str

    return anytype


def openurl_mysql(url, filetype=None):
    import MySQLdb as mysql

    url = urlparse(url.given)
    dbname = url.path[1:]
    conn = mysql.connect(
                user=url.username,
                database=dbname,
                host=url.hostname,
                port=url.port or 3306,
                password=url.password,
                use_unicode=True,
                charset='utf8')

    return MyTablesSheet(dbname+"_tables", sql=SQL(conn), schema=dbname)


class SQL:
    def __init__(self, conn):
        self.conn = conn

    def cur(self, qstr):
        cur = self.conn.cursor()
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
        name, type, *_ = coldesc
        sheet.addColumn(ColumnItem(name, i, type=codeToType(type, name)))


# rowdef: (table_name, ncols)
class MyTablesSheet(Sheet):
    rowtype = 'tables'

    def reload(self):
        qstr = f'''
            select
                t.table_name,
                column_count.ncols,
                t.table_rows as est_nrows
            from
                information_schema.tables t,
                (
                    select
                        table_name,
                        count(column_name) as ncols
                    from
                        information_schema.columns
                    where
                        table_schema = '{self.schema}'
                    group by
                        table_name
                ) as column_count
            where
                t.table_name = column_count.table_name;
        '''

        with self.sql.cur(qstr) as cur:
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
        return MyTable(self.name+"."+row[0], source=row[0], sql=self.sql)


# rowdef: tuple of values as returned by fetchone()
class MyTable(Sheet):
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
