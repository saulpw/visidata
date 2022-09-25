from visidata import vd, Sheet, options, Column, asyncthread, Progress, PivotGroupRow, ENTER

from visidata.loaders._pandas import PandasSheet
from visidata.pivot import PivotSheet

class DataFrameRowSliceAdapter:
    """Tracks original dataframe and a boolean row mask

    This is a workaround to (1) save memory (2) keep id(row)
    consistent when iterating, as id() is used significantly
    by visidata's selectRow implementation.
    """
    def __init__(self, df, mask):
        import pandas as pd
        import numpy as np
        if not isinstance(df, pd.DataFrame):
            vd.fail('%s is not a dataframe' % type(df).__name__)
        if not isinstance(mask, pd.Series):
            vd.fail('mask %s is not a Series' % type(mask).__name__)
        if df.shape[0] != mask.shape[0]:
            vd.fail('dataframe and mask have different shapes (%s vs %s)' % (df.shape[0], mask.shape[0]))

        self.df = df
        self.mask_bool = mask  # boolean mask
        self.mask_iloc = np.where(mask.values)[0]  # integer indexes corresponding to mask
        self.mask_count = mask.sum()

    def __len__(self):
        return self.mask_count

    def __getitem__(self, k):
        if isinstance(k, slice):
            import pandas as pd
            new_mask = pd.Series(False, index=self.df.index)
            new_mask.iloc[self.mask_iloc[k]] = True
            return DataFrameRowSliceAdapter(self.df, new_mask)
        return self.df.iloc[self.mask_iloc[k]]

    def __iter__(self):
        # With the internal selection API used by PandasSheet,
        # this should no longer be needed and can be replaced by
        # DataFrameAdapter(self.df[self.mask_iloc])
        return DataFrameRowSliceIter(self.df, self.mask_iloc)

    def __getattr__(self, k):
        # This is trouble ..
        return getattr(self.df[self.mask_bool], k)

class DataFrameRowSliceIter:
    def __init__(self, df, mask_iloc, index=0):
        self.df = df
        self.mask_iloc = mask_iloc
        self.index = index

    def __next__(self):
        # Accessing row of original dataframe, to ensure
        # that no copies are made and id() of selected rows
        # will match original dataframe's rows
        if self.index >= self.mask_iloc.shape[0]:
            raise StopIteration()
        row = self.df.iloc[self.mask_iloc[self.index]]
        self.index += 1
        return row

class PandasFreqTableSheet(PivotSheet):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'  # rowdef FreqRow(keys, sourcerows)

    def __init__(self, sheet, *groupByCols):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in groupByCols))
        super().__init__(fqcolname, groupByCols, [], source=sheet)
        self.largest = 1

    def selectRow(self, row):
        # Select all entries in the bin on the source sheet.
        # Use the internally defined _selectByLoc to avoid
        # looping which causes a significant performance hit.
        self.source._selectByILoc(row.sourcerows.mask_iloc, selected=True)
        # then select the bin itself on this sheet
        return super().selectRow(row)

    def unselectRow(self, row):
        self.source._selectByILoc(row.sourcerows.mask_iloc, selected=False)
        return super().unselectRow(row)

    def updateLargest(self, grouprow):
        self.largest = max(self.largest, len(grouprow.sourcerows))

    @asyncthread
    def reload(self):
        'Generate frequency table then reverse-sort by length.'
        import pandas as pd

        # Note: visidata's base FrequencyTable bins numeric data in ranges
        # (e.g. as a histogram). We currently don't provide support for this
        # for PandasSheet, although we could implement it with a pd.Grouper
        # that operates similarly to pd.cut.
        super().initCols()

        df = self.source.df.copy()

        # Implementation (special case): for one row, this degenerates
        # to .value_counts(); however this does not order in a stable manner.
        # if len(self.groupByCols) == 1:
        #     this_column = df.loc[:, str(self.groupByCols[0].name)]
        #     value_counts = this_column.value_counts()
        if len(self.groupByCols) >= 1:
            # Implementation (1): add a dummy column to aggregate over in a pd.pivot_table.
            # Is there a way to avoid having to mutate the dataframe? We can delete the
            # column afterwards but we do incur the overhead of block consolidation.
            _pivot_count_column = "__vd_pivot_count"
            if _pivot_count_column not in df.columns:
                df[_pivot_count_column] = 1
            # Aggregate count over columns to group, and then apply a stable sort
            value_counts = df.pivot_table(
                index=[c.name for c in self.groupByCols],
                values=_pivot_count_column,
                aggfunc="count"
            )[_pivot_count_column].sort_values(ascending=False, kind="mergesort")
            # TODO: it seems that the ascending=False causes this to do a "reversed stable sort"?
            # TODO: possibly register something to delete this column as soon as
            # we exit visidata?
            # del df["__vd_pivot_count"]

            # Implementation (2) which does not require adding a dummy column:
            # Compute cross-tabulation to get counts, and sort/remove zero-entries.
            # Note that this is not space-efficient: the initial cross-tabulation will
            # have space on the order of product of number of unique elements for each
            # column, even though its possible the combinations present are sparse
            # and most combinations have zero count.
            # this_column = df.loc[:, str(self.groupByCols[0].name)]
            # value_counts = pd.crosstab(this_column, [df.df[c.name] for c in self.groupByCols[1:]])
            # value_counts = value_counts.stack(list(range(len(self.groupByCols) - 1)))
            # value_counts = value_counts.loc[value_counts > 0].sort_values(ascending=False)
        else:
            vd.fail("Unable to do FrequencyTable, no columns to group on provided")

        # add default bonus columns
        for c in [
                    Column('count', type=int,
                           getter=lambda col,row: len(row.sourcerows)),
                    Column('percent', type=float,
                           getter=lambda col,row: len(row.sourcerows)*100/df.shape[0]),
                    Column('histogram', type=str,
                           getter=lambda col,row: options.disp_histogram*(options.disp_histolen*len(row.sourcerows)//value_counts.max()),
                           width=options.disp_histolen+2),
                    ]:
            self.addColumn(c)

        for element in Progress(value_counts.index):
            if len(self.groupByCols) == 1:
                element = (element,)
            elif len(element) != len(self.groupByCols):
                vd.fail('different number of index cols and groupby cols (%s vs %s)' % (len(element), len(self.groupByCols)))

            mask = df[self.groupByCols[0].name] == element[0]
            for i in range(1, len(self.groupByCols)):
                mask = mask & (df[self.groupByCols[i].name] == element[i])

            self.addRow(PivotGroupRow(
                element,
                (0, 0),
                DataFrameRowSliceAdapter(df, mask),
                {}
            ))

    def openRow(self, row):
        return self.source.expand_source_rows(row)

@Sheet.api
def expand_source_rows(sheet, row):
    """Support for expanding a row of frequency table to underlying rows"""
    if row.sourcerows is None:
        vd.fail("no source rows")
    return PandasSheet(sheet.name, vd.valueNames(row.discrete_keys, row.numeric_key), source=row.sourcerows)

PandasSheet.addCommand('F', 'freq-col', 'vd.push(PandasFreqTableSheet(sheet, cursorCol))', 'open Frequency Table grouped on current column, with aggregations of other columns')
PandasSheet.addCommand('gF', 'freq-keys', 'vd.push(PandasFreqTableSheet(sheet, *keyCols))', 'open Frequency Table grouped by all key columns on source sheet, with aggregations of other columns')

PandasFreqTableSheet.options.numeric_binning = False

vd.addGlobals({
        'PandasFreqTableSheet': PandasFreqTableSheet,
        })
