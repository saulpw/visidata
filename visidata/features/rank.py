import itertools

from visidata import Sheet, ListAggregator, SettableColumn
from visidata import vd, anytype, asyncthread, Progress

class RankAggregator(ListAggregator):
    '''
    Ranks start at 1, and each group's rank is 1 higher than the previous group.
    When elements are tied in ranking, each of them gets the same rank.
    '''
    def aggregate(self, col, rows) -> [int]:
        return self.aggregate_list(col, rows)

    def aggregate_list(self, col, rows) -> [int]:
        if not col.sheet.keyCols:
            vd.error('ranking requires one or more key columns')
        return self.rank(col, rows)

    def rank(self, col, rows):
        if col.keycol:
            vd.warning('rank aggregator is uninformative for key columns')
        def _key_progress(prog):
            def identity(val):
                prog.addProgress(1)
                return val
            return identity
        with Progress(gerund='ranking', total=4*col.sheet.nRows) as prog:
            p = _key_progress(prog) # increment progress every time p() is called
            # compile row data, for each row a list of tuples: (group_key, rank_key, rownum)
            rowdata = [(col.sheet.rowkey(r), col.getTypedValue(r), p(rownum)) for rownum, r in enumerate(rows)]
            # sort by row key and column value to prepare for grouping
            # If the column is in descending order, use descending order for within-group ranking.
            reverse = next((r for (c, r) in col.sheet.ordering if c == col or c == col.name), False)
            try:
                rowdata.sort(reverse=reverse, key=p)
                if reverse:
                    vd.status('ranking {col.name} in descending order')
            except TypeError as e:
                vd.fail(f'elements in a ranking column must be comparable: {e.args[0]}')
            rowvals = []
            #group by row key
            for _, group in itertools.groupby(rowdata, key=lambda v: v[0]):
                # within a group, the rows have already been sorted by col_val
                group = list(group)
                # rank each group individually
                group_ranks = rank_sorted_iterable([p(col_val) for _, col_val, rownum in group])
                rowvals += [(rownum, rank) for (_, _, rownum), rank in zip(group, group_ranks)]
            # sort by unique rownum, to make rank results match the original row order
            rowvals.sort(key=p)
            rowvals = [ rank for rownum, rank in rowvals ]
        return rowvals

vd.aggregators['rank'] = RankAggregator('rank', anytype, helpstr='list of ranks, when grouping by key columns', listtype=int)

def rank_sorted_iterable(vals_sorted) -> [int]:
    '''*vals_sorted* is an iterable whose elements form one or more groups.
    The iterable must already be sorted.'''

    ranks = []
    val_groups = itertools.groupby(vals_sorted)
    for rank, (_, val_group) in enumerate(val_groups, 1):
        for _ in val_group:
            ranks.append(rank)
    return ranks

@Sheet.api
@asyncthread
def addcol_sheetrank(sheet, rows):
    '''
    Each row is ranked within its sheet. Rows are ordered by the
    value of their key columns.
    '''
    if not sheet.keyCols:
        vd.error('ranking requires one or more key columns')
    colname = f'{sheet.name}_sheetrank'
    c = SettableColumn(name=colname, type=int)
    sheet.addColumnAtCursor(c)
    def _key_progress(prog):
        def identity(val):
            prog.addProgress(1)
            return val
        return identity
    with Progress(gerund='ranking', total=5*sheet.nRows) as prog:
        p = _key_progress(prog) # increment progress every time p() is called
        ordering = [(col, reverse) for (col, reverse) in sheet.ordering if col.keycol]
        rowkeys = [(sheet.rowkey(r), p(rownum), r) for rownum, r in enumerate(rows)]
        if ordering:
            vd.status('using custom ordering for keycol sort')
            keycols_ordered = [col for (col, reverse) in ordering]
            keycols_unordered = [keycol for keycol in sheet.keyCols if not keycol in keycols_ordered]
            ordering += [(keycol, False) for keycol in keycols_unordered]
            def _sortkey(e): # sort the rows by using the column
                p(None)
                return sheet.sortkey(e[2], ordering=ordering)
            rowkeys.sort(key=_sortkey)
        else:
            rowkeys.sort(key=p)
        ranks = rank_sorted_iterable([p(rowkey) for rowkey, _, _ in rowkeys])
        row_ranks = sorted(zip((rownum for _, rownum, _ in rowkeys), ranks), key=p)
        row_ranks = [rank for rownum, rank in row_ranks]
        c.setValues(sheet.rows, *[p(row_rank) for row_rank in row_ranks])

Sheet.addCommand('', 'addcol-rank-sheet', 'sheet.addcol_sheetrank(rows)', 'add column with the rank of each row based on its key columns')
