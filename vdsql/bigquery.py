from visidata import vd, VisiData, Sheet, AttrColumn
from . import IbisTableIndexSheet, IbisConnectionPool

import ibis
import ibis.expr.operations as ops


@VisiData.api
def openurl_bigquery(vd, p, filetype=None):
    vd.configure_ibis()
    vd.configure_bigquery()
    return BigqueryDatabaseIndexSheet(p.name, source=p, ibis_con=None)

vd.openurl_bq = vd.openurl_bigquery


@VisiData.api
def configure_bigquery(vd):
    from ibis.backends.base import _connect

    @_connect.register(r"bigquery://(?P<project_id>[^/]+)(?:/(?P<dataset_id>.+))?", priority=13)
    def _(_: str, *, project_id: str, dataset_id: str):
        """Connect to BigQuery with `project_id` and optional `dataset_id`."""
        import ibis
        return ibis.bigquery.connect(project_id=project_id, dataset_id=dataset_id or "")

    @ibis.bigquery.add_operation(ops.TimestampDiff)
    def bq_timestamp_diff(t, expr):
        op = expr.op()
        left = t.translate(op.left)
        right = t.translate(op.right)
        return f"TIMESTAMP_DIFF({left}, {right}, SECOND)"

    @ibis.bigquery.add_operation(ops.ToIntervalUnit)
    def bq_to_interval_unit(t, expr):
        op = expr.op()
        return t.translate(op.arg)


class BigqueryDatabaseIndexSheet(Sheet):
    rowtype = 'databases'  # rowdef: DatasetListItem
    columns = [
#        AttrColumn('project', width=0),
        AttrColumn('dataset_id'),
        AttrColumn('friendly_name'),
        AttrColumn('full_dataset_id', width=0),
        AttrColumn('labels'),
    ]
    nKeys = 1

    @property
    def con(self):
        if not self.ibis_con:
            import ibis
            self.ibis_con = ibis.bigquery.connect()
            self.ibis_con.data_project = self.source.name
        return self.ibis_con

    def iterload(self):
        yield from self.con.client.list_datasets(project=self.source.name)

    def openRow(self, row):
        return IbisTableIndexSheet(row.dataset_id,
                                   database_name=self.source.name+'.'+row.dataset_id,
                                   ibis_con=self.con,
                                   ibis_conpool=IbisConnectionPool(f"{self.source}/{row.dataset_id}"),
                                   source=row,
                                   filetype=None)


