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
    def iterload(self):
        self.query = deepcopy(self.query)  # fresh connection
        q = self.query.sort_by([(col.ibis_col, not rev) for col, rev in self._ordering])

        tbl = q.execute()

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

IbisSqliteSheet.addCommand('F', 'freq-col', 'vd.push(groupBy([cursorCol]))')
IbisSqliteSheet.addCommand('gF', 'freq-keys', 'vd.push(groupBy(keyCols))')
