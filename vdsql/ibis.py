from copy import copy
from visidata import VisiData, Sheet, IndexSheet, vd, date, anytype, vlen, clipdraw, colors, stacktrace
from visidata import ItemColumn, AttrColumn, Column, TextSheet, asyncthread, wrapply

vd.option('disp_ibis_sidebar', '', 'sidebar to display')


def dtype_to_type(dtype):
    import numpy as np
    # Find the underlying numpy dtype for any pandas extension dtypes
    dtype = getattr(dtype, 'numpy_dtype', dtype)
    try:
        if np.issubdtype(dtype, np.integer):
            return int
        if np.issubdtype(dtype, np.floating):
            return float
        if np.issubdtype(dtype, np.datetime64):
            return date
    except TypeError:
        # For categoricals and other pandas-defined dtypes
        pass
    return anytype


@VisiData.api
def open_ibis(vd, p):
    import ibis
    vd.aggregator('collect', ibis.expr.types.AnyValue.collect, 'collect a list of values')
    ibis.options.verbose_log = vd.status
    return IbisTableIndexSheet(p.name, source=p, filetype=None, database_name=None, ibis_con=None)


vd.open_duckdb = vd.open_ibis
vd.open_ddb = vd.open_ibis


@VisiData.api
def openurl_bigquery(vd, p, filetype=None):
    return BigqueryDatabaseIndexSheet(p.name, source=p, ibis_con=None)

vd.openurl_bq = openurl_bigquery


class IbisTableIndexSheet(IndexSheet):
    @property
    def con(self):
        if not self.ibis_con:
            import ibis
            self.ibis_con = ibis.connect(str(self.source))

        return self.ibis_con

    def iterload(self):
        import ibis

        con = self.con
        if self.database_name:
            con.set_database(self.database_name)

        # use the actual count instead of the returned limit
        nrows_col = self.column('rows')
        nrows_col.expr = 'countRows'
        nrows_col.width += 3

        for tblname in con.list_tables():
            tbl = con.table(tblname)
            q = ibis.table(tbl.schema(), name=tblname)

            yield IbisTableSheet(*self.names, tblname,
                    ibis_source=self.source,
                    ibis_filetype=self.filetype,
                    ibis_con=self.con,
                    database_name=self.database_name,
                    source=self.source,
                    query=q)




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
            self.ibis_con = ibis.bigquery.connect(project_id=self.source.name)
        return self.ibis_con

    def iterload(self):
        yield from self.con.client.list_datasets()

    def openRow(self, row):
        return IbisTableIndexSheet(row.dataset_id, database_name=row.dataset_id, ibis_con=self.con, source=row, filetype=None)



class IbisColumn(ItemColumn):
    pass


@IbisColumn.api
@asyncthread
def memo_aggregate(col, agg, rows):
    'Show aggregated value in status, and add ibis expr to memory for use later.'

    aggexpr = col.ibis_aggr(agg.name)  # ignore rows, do over whole query

    aggval = col.sheet.con.execute(aggexpr)
    typedval = wrapply(agg.type or col.type, aggval)
    dispval = col.format(typedval)
    k = col.name+'_'+agg.name
    vd.status(f'{k}={dispval}')
    vd.memory[k] = aggval
    # store aggexpr somewhere to use in later subquery



class IbisTableSheet(Sheet):
    @property
    def con(self):
        if not self.ibis_con:
            import ibis
            self.ibis_con = ibis.connect(str(self.source))

        return self.ibis_con


    def cycle_sidebar(self):
        sidebars = ['', 'ibis_sql', 'ibis_expr', 'ibis_substrait']
        try:
            i = sidebars.index(vd.options.disp_ibis_sidebar)+1
        except ValueError:
            vd.warning(f'unknown sidebar option {vd.options.disp_ibis_sidebar}, resetting')
            i = 0
        vd.options.disp_ibis_sidebar = sidebars[i%len(sidebars)]

    @property
    def sidebar(self):
        return str(getattr(self, self.options.disp_ibis_sidebar, ''))

    @property
    def ibis_expr(self):
        q = self.query
        projections = []
        mutates = {}
        for c in self.visibleCols:
            ibis_col = c.get_ibis_col(q)
            if ibis_col is not None:
                mutates[c.name] = ibis_col
                projections.append(ibis_col)

        if projections:
            q = q.projection(projections)

        q = q.mutate(**mutates)

        if self.ibis_filters:
            q = q.filter(self.ibis_filters)

        if self._ordering:
            q = q.sort_by([(col.get_ibis_col(self.query), not rev) for col, rev in self._ordering])

        return q

    @property
    def ibis_sql(self):
        import sqlparse
        sqlstr = str(self.con.compile(self.ibis_expr).compile(compile_kwargs={'literal_binds': True}))
        return sqlparse.format(sqlstr, reindent=True, keyword_case='upper')

    @property
    def ibis_substrait(self):
        from ibis_substrait.compiler.core import SubstraitCompiler
        compiler = SubstraitCompiler()
        return compiler.compile(self.ibis_expr)

    def iterload(self):
        self.query_result = self.con.execute(self.query.mutate(__n__=lambda t: t.count()))

        self.options.disp_rstatus_fmt = self.options.disp_rstatus_fmt.replace('nRows', 'countRows')

        oldkeycols = {c.name:c for c in self.keyCols}
        self.columns = []
        self._nrows_col = -1

        for i, colname in enumerate(self.query_result.columns):
            keycol=oldkeycols.get(colname, Column()).keycol
            if i < self.nKeys:
                keycol = i+1

            if colname == '__n__':
                self._nrows_col = i+1
                continue

            self.addColumn(IbisColumn(colname, i+1,
                           type=dtype_to_type(self.query_result.dtypes[i]),
                           keycol=keycol,
                           ibis_name=colname))

        yield from self.query_result.itertuples()

    @property
    def countRows(self):
        if not self.rows or self._nrows_col < 0:
            return None
        return self.rows[0][self._nrows_col]  # __n__

    def groupBy(self, groupByCols):
        aggr_cols = [c.ibis_col.count() for c in groupByCols]
        for c in self.visibleCols:
            aggr_cols.extend(c.ibis_aggrs)
        groupq = self.query.aggregate(aggr_cols,
                                 by=[c.ibis_col for c in groupByCols])

        return IbisTableSheet(self.name, *(col.name for col in groupByCols), 'freq',
                             ibis_con=self.ibis_con,
                             ibis_source=self.ibis_source,
                             source=self,
                             groupByCols=groupByCols,
                             query=groupq,
                             nKeys=len(groupByCols))

    def openRow(self, row):
        vs = copy(self.source)
        vs.names = list(vs.names) + ['_'.join(str(x) for x in self.rowkey(row))]
        vs.query = self.source.query.filter([
            self.groupByCols[0].ibis_col == self.rowkey(row)[0]
            # matching key of grouped columns
        ])
        return vs

    def unfurl_col(self, col):
        vs = copy(self)
        vs.names = [self.name, col.name, 'unfurled']
        vs.query = self.query.mutate(**{col.name:col.ibis_col.unnest()})
        vs.cursorVisibleColIndex = self.cursorVisibleColIndex
        return vs

    def openJoin(self, others, jointype=''):
        sheets = [self] + others

        sheets[1:] or vd.fail("join requires more than 1 sheet")

        if jointype == 'append':
            q = self.query
            for other in others:
                q = q.union(other.query)
            return IbisTableSheet('&'.join(vs.name for vs in sheets), query=q, ibis_source=self.ibis_source, ibis_con=self.ibis_con)

        for s in sheets:
            s.keyCols or vd.fail(f'{s.name} has no key cols to join')

        if jointype == 'extend':
            jointype = 'left'

        q = self.query
        for other in others:
            preds = [(a.ibis_col == b.ibis_col) for a, b in zip(self.keyCols, other.keyCols)]
            q = q.join(other.query, predicates=preds, how=jointype)

        return IbisTableSheet('+'.join(vs.name for vs in sheets), sources=sheets, query=q, ibis_source=self.ibis_source, ibis_con=self.ibis_con)


@Column.property
def ibis_col(col):
    return col.get_ibis_col(col.sheet.query)


@Column.api
def get_ibis_col(col, query):
    import ibis.expr.datatypes as dt
    import ibis.common.exceptions

    if not hasattr(col, 'ibis_name'):
        return

    r = None
    try:
        r = query.get_column(col.ibis_name)
    except (ibis.common.exceptions.IbisTypeError, AttributeError):
        r = query.get_column(col.name)

    if r is None:
        return r

    if col.type is int:
        r = r.cast(dt.int)
    elif col.type is float:
        r = r.cast(dt.float)
    elif col.type is date:
        r = r.cast(dt.date)

    r = r.name(col.name)
    return r


@Column.property
def ibis_aggrs(col):
    return [col.ibis_aggr(aggname) for aggname in (col.aggstr or '').split()]


@Column.api
def ibis_aggr(col, aggname):
    return getattr(col.ibis_col, aggname)().name(f'{aggname}_{col.name}')


IbisTableSheet.init('ibis_filters', list, copy=True)
IbisTableSheet.init('ibis_selection', list, copy=True)
IbisTableSheet.init('_sqlscr', lambda: None, copy=False)
IbisTableSheet.init('query_result', lambda: None, copy=False)
IbisTableSheet.init('ibis_con', lambda: None, copy=True)

IbisTableSheet.addCommand('F', 'freq-col', 'vd.push(groupBy([cursorCol]))')
IbisTableSheet.addCommand('gF', 'freq-keys', 'vd.push(groupBy(keyCols))')

IbisTableSheet.addCommand('gt', 'stoggle-rows', 'toggle(rows)\nfor i in range(len(ibis_selection)): ibis_selection[i] = ~ibis_selection[i]', 'select rows matching current cell in current column')
IbisTableSheet.addCommand(',', 'select-equal-cell', 'ibis_selection.append(cursorCol.ibis_col == cursorTypedValue); select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisTableSheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getDisplayValue(r) == c.getDisplayValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
#IbisTableSheet.addCommand('z,', 'select-exact-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisTableSheet.addCommand('gz,', 'select-exact-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
IbisTableSheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.ibis_filters.extend(vs.ibis_selection); vs.ibis_selection.clear(); vd.push(vs)', 'open duplicate sheet with only selected rows'),
IbisTableSheet.addCommand('v', 'sidebar-cycle', 'cycle_sidebar()')

IbisTableSheet.addCommand('', 'open-sidebar', 'vd.push(TextSheet(name, options.disp_ibis_sidebar, source=sidebar.splitlines()))')

vd.addMenuItem('View', 'Sidebar', 'cycle', 'sidebar-cycle')
vd.addMenuItem('View', 'Sidebar', 'open', 'open-sidebar')
