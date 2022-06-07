from copy import copy, deepcopy
from visidata import VisiData, Sheet, IndexSheet, vd, date, anytype, vlen, clipdraw, colors, stacktrace
from visidata import ItemColumn, AttrColumn, Column, TextSheet

vd.option('color_sidebar', 'black on 114 blue', 'color of sidebar')
vd.option('disp_sidebar', '', 'sheet attribute to display in a sidebar overlay')


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
def openurl_ibis(vd, p, filetype=None):
    import ibis
    ibis.options.verbose_log = vd.status
    return IbisSqliteIndexSheet(p.name, source=p, filetype=filetype)


@VisiData.api
def open_ibis(vd, p):
    import ibis
    ibis.options.verbose_log = vd.status
    return IbisSqliteIndexSheet(p.name, source=p, filetype=None)


class IbisSqliteIndexSheet(IndexSheet):
    def iterload(self):
        import ibis
        if self.filetype:
            con = getattr(ibis, self.filetype).connect(str(self.source))
        else:
            con = ibis.connect(str(self.source))

        for tblname in con.list_tables():
            yield IbisSheet(self.source.name, tblname, source=self.source, query=con.table(tblname))


class IbisColumn(ItemColumn):
    pass


def iterwraplines(lines, width=80):
    import textwrap
    for line in lines:
        yield from textwrap.wrap(line, width=width, subsequent_indent='  ')


def clipbox(scr, lines, attr, title=''):
    scr.erase()
    scr.bkgd(attr)
    scr.box()
    h, w = scr.getmaxyx()
    clipdraw(scr, 0, w-len(title)-6, f"| {title} |", attr)
    for i, line in enumerate(lines):
        clipdraw(scr, i+1, 2, line, attr)


class IbisSheet(Sheet):
    def draw(self, scr):
        super().draw(scr)

        try:
            sidebar_text = str(getattr(self, self.options.disp_sidebar, '')).splitlines()
        except Exception as e:
            vd.exceptionCaught(e)
            sidebar_text = stacktrace(e)

        if not sidebar_text:
            return

        h, w = scr.getmaxyx()
        maxh, maxw = 0, 0

        lines = list(iterwraplines(sidebar_text, width=w//2))

        maxh = min(h-2, len(lines)+2)
        maxw = min(w//2, max(map(len, lines))+4)

        sidebar_scr = scr.derwin(maxh, maxw, h-maxh-1, w-maxw-1)
        clipbox(sidebar_scr, lines, colors.color_sidebar, title=self.options.disp_sidebar)

    def cycle_sidebar(self):
        sidebars = ['', 'ibis_sql', 'ibis_expr', 'ibis_substrait']
        try:
            i = sidebars.index(self.options.disp_sidebar)+1
        except ValueError:
            i = 0

        vd.options.disp_sidebar = sidebars[i % len(sidebars)]

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

        q = q.projection(projections)
#        q = q.mutate(**mutates)

        if self.ibis_filters:
            q = q.filter(self.ibis_filters)

        if self._ordering:
            q = q.sort_by([(col.get_ibis_col(q), not rev) for col, rev in self._ordering])

        return q

    @property
    def ibis_sql(self):
        import sqlparse
        sqlstr = str(self.ibis_expr.compile().compile(compile_kwargs={'literal_binds': True}))
        return sqlparse.format(sqlstr, reindent=True, keyword_case='upper')

    @property
    def ibis_substrait(self):
        from ibis_substrait.compiler.core import SubstraitCompiler
        compiler = SubstraitCompiler()
        return compiler.compile(self.ibis_expr)

    def iterload(self):
        self.query = deepcopy(self.ibis_expr)  # fresh connection
        self.query._find_backend().reconnect()

        self.query_result = self.query.execute()

        self.columns = []
        for i, colname in enumerate(self.query_result.columns):
            self.addColumn(IbisColumn(colname, i+1,
                           type=dtype_to_type(self.query_result.dtypes[i]),
                           keycol=(i+1) if i < self.nKeys else None,
                           ibis_name=colname))

        yield from self.query_result.itertuples()

    def groupBy(self, groupByCols):
        aggr_cols = [c.ibis_col.count() for c in groupByCols]
        for c in self.visibleCols:
            aggr_cols.extend(c.ibis_aggrs)
        groupq = self.query.aggregate(aggr_cols,
                                 by=[c.ibis_col for c in groupByCols])

        return IbisSheet(self.name, *(col.name for col in groupByCols), 'freq',
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

    def openJoin(self, others, jointype=''):
        sheets = [self] + others

        sheets[1:] or vd.fail("join requires more than 1 sheet")

        if jointype == 'append':
            q = self.query
            for other in others:
                q = q.union(other.query)
            return IbisSheet('&'.join(vs.name for vs in sheets), query=q)

        for s in sheets:
            s.keyCols or vd.fail(f'{s.name} has no key cols to join')

        if jointype == 'extend':
            jointype = 'left'

        q = self.query
        for other in others:
            preds = [(a.ibis_col == b.ibis_col) for a, b in zip(self.keyCols, other.keyCols)]
            q = q.join(other.query, predicates=preds, how=jointype)

        return IbisSheet('+'.join(vs.name for vs in sheets), sources=sheets, query=q)


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
    return [getattr(col.ibis_col, aggname)() for aggname in (col.aggstr or '').split()]


IbisSheet.init('ibis_filters', list, copy=True)
IbisSheet.init('ibis_selection', list, copy=True)
IbisSheet.init('_sqlscr', lambda: None, copy=False)
IbisSheet.init('query_result', lambda: None, copy=False)

IbisSheet.addCommand('F', 'freq-col', 'vd.push(groupBy([cursorCol]))')
IbisSheet.addCommand('gF', 'freq-keys', 'vd.push(groupBy(keyCols))')

IbisSheet.addCommand(',', 'select-equal-cell', 'ibis_selection.append(cursorCol.ibis_col == cursorTypedValue); select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisSheet.addCommand('g,', 'select-equal-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getDisplayValue(r) == c.getDisplayValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
#IbisSheet.addCommand('z,', 'select-exact-cell', 'select(gatherBy(lambda r,c=cursorCol,v=cursorTypedValue: c.getTypedValue(r) == v), progress=False)', 'select rows matching current cell in current column')
#IbisSheet.addCommand('gz,', 'select-exact-row', 'select(gatherBy(lambda r,currow=cursorRow,vcols=visibleCols: all([c.getTypedValue(r) == c.getTypedValue(currow) for c in vcols])), progress=False)', 'select rows matching current row in all visible columns')
IbisSheet.addCommand('"', 'dup-selected', 'vs=copy(sheet); vs.name += "_selectedref"; vs.ibis_filters.extend(vs.ibis_selection); vs.ibis_selection.clear(); vd.push(vs)', 'open duplicate sheet with only selected rows'),
IbisSheet.addCommand('v', 'sidebar-cycle', 'cycle_sidebar()')

IbisSheet.addCommand('', 'sidebar-sql', 'vd.options.disp_sidebar="ibis_sql"')
IbisSheet.addCommand('', 'sidebar-substrait', 'vd.options.disp_sidebar="ibis_substrait"')
IbisSheet.addCommand('', 'sidebar-ibis-expr', 'vd.options.disp_sidebar="ibis_expr"')
IbisSheet.addCommand('', 'sidebar-none', 'vd.options.disp_sidebar=""')

IbisSheet.addCommand('', 'open-ibis-expr', 'vd.push(TextSheet(name, "ibis", source=str(ibis_expr).splitlines()))')
IbisSheet.addCommand('', 'open-ibis-sql', 'vd.push(TextSheet(name, "sql", source=ibis_sql.splitlines()))')
IbisSheet.addCommand('', 'open-ibis-substrait', 'vd.push(TextSheet(name, "substrait", source=ibis_substrait.splitlines()))')

vd.addMenuItem('View', 'Sidebar', 'None', 'sidebar-none')
vd.addMenuItem('View', 'Sidebar', 'Ibis expr', 'sidebar-ibis')
vd.addMenuItem('View', 'Sidebar', 'SQL expr', 'sidebar-sql')
vd.addMenuItem('View', 'Sidebar', 'Substrait', 'sidebar-substrait')
vd.addMenuItem('View', 'Sidebar', 'Cycle options', 'sidebar-cycle')
