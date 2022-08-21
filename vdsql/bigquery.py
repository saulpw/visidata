from visidata import vd, VisiData, Sheet, AttrColumn
from . import IbisTableIndexSheet, IbisConnectionPool


@VisiData.api
def openurl_bigquery(vd, p, filetype=None):
    return BigqueryDatabaseIndexSheet(p.name, source=p, ibis_con=None)


vd.openurl_bq = openurl_bigquery


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
