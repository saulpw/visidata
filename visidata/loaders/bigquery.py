from visidata import *


class LazyRowset(dict):
    def __init__(self, tbl, num=None):
        super().__init__()
        self._table = tbl
        self._len = num

    def __len__(self):
        return 25 if self._len is None else self._len

    def __iter__(self):
        for v in self.values():
            yield v

    def __getitem__(self, k):
        if isinstance(k, slice):
            job = None
            ret = []
            rng = range(len(self))[k]
            for r in rng:
                v = self.get(r, None)
                if v is None:
                    if job is None:
                        job = self._table.doQuery(rng.start, rng.stop-rng.start+1)
                    self[r] = job
                    ret.append(job)
                else:
                    ret.append(v)
            return ret
        else:
            v = self.get(k, None)  # this makes None invalid row value (which seems reasonable)
            if v is None:
                job = self._table.doQuery(k, 1)
                self[k] = k
                return job
            return v


def open_bigquery(p):
    project, dataset = p.fqpn.split(':')
    return BigQueryTableList(p.fqpn, project=project, datasetName=dataset)

class BigQueryTableList(Sheet):
    columns = [
        ColumnAttr('table_id'),
        ColumnAttr('location'),
        ColumnAttr('num_rows', type=int),
        ColumnAttr('friendly_name'),
        ColumnAttr('description'),
        ColumnAttr('num_bytes', type=int),
        ColumnAttr('created', type=date),
        ColumnAttr('modified', type=date),
    ]
    nKeys = 1
    commands = [
        Command(ENTER, 'vd.push(BQTable(client, cursorRow))', 'push this table'),
    ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from google.cloud import bigquery
        self.client = bigquery.Client()
        self.__dataset_ref = self.client.dataset(self.datasetName, project=self.project)
        self._dataset = None

    @property
    def dataset(self):
        if self._dataset is None:
            self._dataset = self.client.get_dataset(self.__dataset_ref)
        return self._dataset

    @async
    def reload(self):
        tables = list(self.client.list_tables(self.dataset))

        self.rows = []
        for tbl in Progress(tables):
            tref = self.dataset.table(tbl.table_id)
            self.rows.append(self.client.get_table(tref))


BQTypes = {
    'STRING': anytype,
    'INTEGER': int,
}

def columnsFromSchema(schema, prefix='', ret=None):
    if ret is None:
        ret = []

    for field in schema:
        name = (prefix+'.'+field.name) if prefix else field.name
        if field.field_type == 'RECORD':
            columnsFromSchema(field.fields, prefix=name, ret=ret)
        else:
            c = ColumnItem(name, field.name, type=BQTypes.get(field.field_type, anytype))
            if prefix:
                c = SubrowColumn(c, prefix)
            ret.append(c)

    return ret


# client, query
class BigQueryResult(Sheet):
    commands = [
        Command('F', 'vd.push(BigQuerySQL(source=SheetFreqTable(sheet, cursorCol)))', 'push freq for this column'),
    ]

    def sqlFROM(self):
        return '.'.join([self.table.project, self.table.dataset_id, self.table.table_id])

    @async
    def doQuery(self, start, limit):
        'partial query'
        from google.cloud import bigquery
        job_config = bigquery.job.QueryJobConfig()
        job_config.dry_run = True
        my_job = self.client.query(self.query, job_config=job_config)
        status('cost: %.02fGB' % (my_job.total_bytes_processed/(2**30)))

        job_config.dry_run = False
        job_config.start_index = start
        job_config.max_results = limit
        my_job = self.client.query(self.query, job_config=job_config)

        result = my_job.result()

        self.result = result
        self.handleResult(result, start, limit)

    def handleResult(self, result, start, limit):
        if not self.columns:
            self.columns = columnsFromSchema(result.schema)

        for i, row in enumerate(Progress(result, total=result.num_results)):
            self.rows[start+i] = row
            if result.total_rows is not None:
                self.rows._len = result.total_rows

    def reload(self):
        self.rows = LazyRowset(self, None) #self.table.num_rows)
        self.columns = []
        self.doQuery(0, 25)


class BQTableListRows(BigQueryResult):
    @async
    def doQuery(self, start, limit):
        result = self.client.list_rows(self.table, start_index=start, max_results=limit)
        self.handleResult(result, start, limit)

    def reload(self):
        self.rows = LazyRowset(self, self.table.num_rows)
        self.columns = columnsFromSchema(self.table.schema)
        self.doQuery(0, 25)


def BQTable(client, tbl):
    return BQTableListRows(tbl.table_id, client=client, table=tbl)

def BigQuerySQL(source):
    # TODO: filter out non-selectable columns
    cols = [getattr(col, 'sql', col.name) for col in source.visibleCols]
    colnames = ', '.join(cname for cname in cols if cname) or '*'

    bqsrc = source
    while bqsrc and not isinstance(bqsrc, BigQueryResult):
        bqsrc = bqsrc.source

    query = 'SELECT ' + colnames
    query += ' FROM `%s` ' % (bqsrc.sqlFROM())

#    query += ' WHERE ' % (source.sqlWHERE())

    groupcols = getattr(source, 'groupby', None)
    if groupcols:
        grouping = ', '.join(getattr(c, 'sql', c.name) for c in groupcols)
        query += ' GROUP BY ' + grouping

    orders = []
    for c, direction in getattr(source, 'orderby', None):
        colsql = getattr(c, 'sql', c.name)
        dirstr = " DESC" if direction < 0 else " ASC"
        if colsql:
            orders.append(colsql + dirstr)

    if orders:
        query += ' ORDER BY ' + ', '.join(orders)

    status(query)
    return BigQueryResult(source.name, client=bqsrc.client, table=bqsrc.table, query=query)

##

globalCommand('g^T', 'vd.push(BigQueryJobs("bigquery_jobs", client=client))')

class BigQueryJobs(Sheet):
    def reload(self):
        self.rows = list(self.client.list_jobs())
