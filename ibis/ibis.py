from copy import copy, deepcopy
from visidata import VisiData, Sheet, IndexSheet, vd, date, anytype, vlen
from visidata import ItemColumn, AttrColumn, Column


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
def open_sqlite_ibis(vd, p):
    import ibis
    ibis.options.verbose_log = vd.status
    return IbisSqliteIndexSheet(p.name, source=p)


class IbisSqliteIndexSheet(IndexSheet):
    def iterload(self):
        import ibis
        con = ibis.sqlite.connect(str(self.source))
        for tblname in con.list_tables():
            yield IbisSqliteSheet(self.source.name, tblname, source=self.source, query=con.table(tblname))


class IbisSqliteSheet(Sheet):
    @property
    def ibis_expr(self):
        q = deepcopy(self.query)  # fresh connection
        q = q.filter(self.ibis_filters)
        q = q.sort_by([(col.ibis_col, not rev) for col, rev in self._ordering])
        return q

    @property
    def ibis_sql(self):
        return str(self.query.compile().compile(compile_kwargs={'literal_binds': True}))

    def iterload(self):
        self.query = self.ibis_expr

        vd.debug(self.ibis_sql)
        tbl = self.query.execute()

        self.columns = []
        for i, colname in enumerate(tbl.columns):
            self.addColumn(ItemColumn(colname, i+1,
                           type=dtype_to_type(tbl.dtypes[i]),
                           keycol=(i+1) if i < self.nKeys else None,
                           ibis_name=colname))

        yield from tbl.itertuples()

    def groupBy(self, groupByCols):
        aggr_cols = [c.ibis_col.count() for c in groupByCols]
        for c in self.visibleCols:
            aggr_cols.extend(c.ibis_aggrs)
        groupq = self.query.aggregate(aggr_cols,
                                 by=[c.ibis_col for c in groupByCols])

        return IbisSqliteSheet(self.name, *(col.name for col in groupByCols), 'freq',
                             source=self,
                             groupByCols=groupByCols,
                             query=groupq,
                             nKeys=len(groupByCols))

    def openRow(self, row):
        vs = copy(self.source)
        vs.name += '_'.join(str(x) for x in self.rowkey(row))
        vs.query = self.source.query.filter([
            self.groupByCols[0].ibis_col == self.rowkey(row)[0]
            # matching key of grouped columns
        ])
        return vs


@Column.property
def ibis_col(col):
    return col.sheet.query.get_column(col.ibis_name)


@Column.property
def ibis_aggrs(col):
    return [getattr(col.ibis_col, aggname)() for aggname in (col.aggstr or '').split()]


IbisSqliteSheet.init('ibis_filters', list, copy=True)

IbisSqliteSheet.addCommand('F', 'freq-col', 'vd.push(groupBy([cursorCol]))')
IbisSqliteSheet.addCommand('gF', 'freq-keys', 'vd.push(groupBy(keyCols))')
IbisSqliteSheet.addCommand('', 'open-ibis-expr', 'vd.push(TextSheet(name, "ibis_expr", source=str(ibis_expr).splitlines()))')
IbisSqliteSheet.addCommand('', 'open-ibis-sql', 'vd.push(TextSheet(name, "ibis_sql", source=str(ibis_expr.compile()).splitlines()))')

IbisSqliteSheet.addCommand(',', 'select-equal-cell', 'ibis_filters.append(cursorCol.ibis_col == cursorTypedValue); select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisSqliteSheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getDisplayValue(r) == c.getDisplayValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
#IbisSqliteSheet.addCommand('z,', 'select-exact-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisSqliteSheet.addCommand('gz,', 'select-exact-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
IbisSqliteSheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vd.push(vs)', 'open duplicate sheet with only selected rows'),

#vd.addMenuItem('View', 'Ibis expression'
