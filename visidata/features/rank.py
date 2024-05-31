import itertools

from visidata import Sheet, ListAggregator, SettableColumn
from visidata import vd, anytype, asyncthread

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
            return None
        return self.rank(col, rows)

    def rank(self, col, rows):
        # compile row data, for each row a list of tuples: (group_key, rank_key, rownum)
        rowdata = [(col.sheet.rowkey(r), col.getTypedValue(r), rownum) for rownum, r in enumerate(rows)]
        # sort by row key and column value to prepare for grouping
        try:
            rowdata.sort()
        except TypeError as e:
            vd.fail(f'elements in a ranking column must be comparable: {e.args[0]}')
        rowvals = []
        #group by row key
        for _, group in itertools.groupby(rowdata, key=lambda v: v[0]):
            # within a group, the rows have already been sorted by col_val
            group = list(group)
            # rank each group individually
            group_ranks = rank_sorted_iterable([col_val for _, col_val, rownum in group])
            rowvals += [(rownum, rank) for (_, _, rownum), rank in zip(group, group_ranks)]
        # sort by unique rownum, to make rank results match the original row order
        rowvals.sort()
        rowvals = [ rank for rownum, rank in rowvals ]
        return rowvals

vd.aggregators['rank'] = RankAggregator('rank', anytype, helpstr='list of ranks, when grouping by key columns', listtype=int)

def rank_sorted_iterable(vals_sorted) -> [int]:
    '''*vals_sorted* is an iterable whose elements form one group.
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
    colname = f'{sheet.name}_sheetrank'
    c = SettableColumn(name=colname, type=int)
    sheet.addColumnAtCursor(c)
    if not sheet.keyCols:
        vd.error('ranking requires one or more key columns')
        return None
    rowkeys = [(sheet.rowkey(r), rownum) for rownum, r in enumerate(rows)]
    rowkeys.sort()
    ranks = rank_sorted_iterable([rowkey for rowkey, rownum in rowkeys])
    row_ranks = sorted(zip((rownum for _, rownum in rowkeys), ranks))
    row_ranks = [rank for rownum, rank in row_ranks]
    c.setValues(sheet.rows, *row_ranks)

Sheet.addCommand('', 'addcol-sheetrank', 'sheet.addcol_sheetrank(rows)', 'add column with the rank of each row based on its key columns')
