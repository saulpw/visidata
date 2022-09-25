import time

from visidata import BaseException, vd, VisiData, Progress

from ._ibis import IbisTableSheet, IbisTableIndexSheet, IbisConnectionPool


@VisiData.api
def openurl_clickhouse(vd, p, filetype=None):
    vd.configure_ibis()
    return IbisTableIndexSheet(p.name, source=p, filetype=None, database_name=None,
                               ibis_conpool=IbisConnectionPool(p), sheet_type=ClickhouseSheet)

vd.openurl_clickhouses = vd.openurl_clickhouse


class ClickhouseSheet(IbisTableSheet):
    @property
    def countRows(self):
        if self.total_rows is not None:
            return self.total_rows
        return super().countRows

    def iterload(self):
        self.preload()
        with self.con as con:
            qid = None
            try:
                if self.query is None:
                    self.query = self.baseQuery(con)

                self.reloadColumns(self.query, start=0)  # columns based on query without metadata
                sqlstr = con.compile(self.query.limit(self.options.ibis_limit or None))

                with Progress(gerund='clickhousing', sheet=self) as prog:
                    settings = {'max_block_size': 10000}
                    self.query_result = con.con.execute_iter(sqlstr, settings, chunk_size=1000, query_id=qid)
                    qid = str(time.time())
                    for row in self.query_result:
                        prog.total = con.con.last_query.progress.total_rows
                        prog.made = con.con.last_query.progress.rows
                        self.total_rows = prog.total
                        yield from row

            except Exception as e:
                raise
            except BaseException:
                if qid:
                    con.con.cancel(qid)


ClickhouseSheet.init('total_rows', lambda: None)

#ClickhouseSheet.class_options.sql_always_count = True
