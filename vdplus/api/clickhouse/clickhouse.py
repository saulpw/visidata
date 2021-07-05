
from visidata import vd, addGlobals, asyncthread, Sheet, ItemColumn
from visidata import *

__all__ = ['openurl_clickhouse']

vd.option('clickhouse_host', '', '')
vd.option('clickhouse_port', 9000, '')

def openurl_clickhouse(p, filetype=None):
    url = urlparse(p.given)
    options.clickhouse_host = url.hostname
    options.clickhouse_port = url.port
    return ClickhouseIndexSheet(p.name, source=p)

BaseSheet.addCommand(ALT+'c', 'open-clickhouse', 'vd.push(vd.clickhouse_queries)')

class ClickhouseQuerySheet(Sheet):
    columns = [
        ColumnItem('name', 0),
        ColumnItem('query', 1),
        ColumnItem('nrows', 2),
        ColumnItem('notes', 3),
    ]
    _rowtype=lambda: ['', '', 0, '']

    def openRow(self, row):
        return ClickhouseSheet(row[0], query=row[1])

@VisiData.lazy_property
def clickhouse_client(vd):
    from clickhouse_driver import Client
    return Client(**options.getall('clickhouse_'))

@VisiData.lazy_property
def clickhouse_queries(self):
    return ClickhouseQuerySheet("queries")


class ClickhouseSheet(Sheet):
    @asyncthread
    def reload(self):
        if isinstance(self.source, ClickhouseSheet):
            vd.clickhouse_client.execute('USE %s' % self.source.dbname)

        self.rows = []
        self.columns = []
        self.result = vd.clickhouse_client.execute(self.query, with_column_types=True)
        result = self.result[0]

        for i, r in enumerate(self.result[1]):
            self.addColumn(ItemColumn(r[0], i))

        for r in result:
            self.addRow(r)

class ClickhouseIndexSheet(IndexSheet):
    @asyncthread
    def reload(self):
        self.rows = []
        for r in vd.clickhouse_client.execute('SHOW DATABASES'):
            self.addRow(ClickhouseDbSheet(r[0], source=self))

class ClickhouseDbSheet(IndexSheet):
    @asyncthread
    def reload(self):
        vd.clickhouse_client.execute('USE %s' % self.name)
        self.rows = []
        for r in vd.clickhouse_client.execute('SHOW TABLES'):
            self.addRow(ClickhouseSheet(r[0], source=self, query='SELECT * FROM %s LIMIT 100' % r[0]))

addGlobals({'openurl_clickhouse': openurl_clickhouse})
