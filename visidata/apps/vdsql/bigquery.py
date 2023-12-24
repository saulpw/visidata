'''
Specify the billing_project_id as the netloc, and the actual dataset_id as the path:

    vdsql bigquery://<billing_project>/<dataset_id>''
'''


from visidata import vd, VisiData, Sheet, AttrColumn
from . import IbisTableSheet, IbisTableIndexSheet, IbisConnectionPool

import ibis
import ibis.expr.operations as ops

@VisiData.api
def openurl_bigquery(vd, p, filetype=None):
    vd.configure_ibis()
    vd.configure_bigquery()
    return BigqueryDatabaseIndexSheet(p.base_stem, source=p, ibis_con=None)

vd.openurl_bq = vd.openurl_bigquery


@VisiData.api
def configure_bigquery(vd):
    @ibis.bigquery.add_operation(ops.TimestampDiff)
    def bq_timestamp_diff(t, expr):
        op = expr.op()
        left = t.translate(op.left)
        right = t.translate(op.right)
        return f"TIMESTAMP_DIFF({left}, {right}, SECOND)"


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
            self.ibis_con = ibis.connect(self.source)
        return self.ibis_con

    def iterload(self):
        yield from self.con.client.list_datasets(project=self.source.name)

    def openRow(self, row):
        return IbisTableIndexSheet(row.dataset_id,
                                   database_name=self.source.name+'.'+row.dataset_id,
                                   ibis_con=self.con,
                                   ibis_conpool=IbisConnectionPool(f"{self.source}/{row.dataset_id}"),
                                   source=row,
                                   filetype=None,
                                   sheet_type=IbisTableSheet)
