import math
import collections

from visidata import *

PandasSheet.addCommand('F', 'freq-col', 'vd.push(PandasSheetFreqTable(sheet, cursorCol))')
PandasSheet.addCommand('gF', 'freq-keys', 'vd.push(PandasSheetFreqTable(sheet, *keyCols))')
# globalCommand('zF', 'freq-rows', 'vd.push(SheetFreqTable(sheet, Column("Total", getter=lambda col,row: "Total")))')
# 
# theme('disp_histogram', '*', 'histogram element character')
# option('disp_histolen', 50, 'width of histogram column')
# option('histogram_bins', 0, 'number of bins for histogram of numeric columns')
# 
# ColumnsSheet.addCommand(ENTER, 'freq-row', 'vd.push(SheetFreqTable(source[0], cursorRow))')

# def valueNames(discrete_vals, numeric_vals):
#     ret = [ '+'.join(str(x) for x in discrete_vals) ]
#     if numeric_vals != (0, 0):
#         ret.append('%s-%s' % numeric_vals)
# 
#     return '+'.join(ret)

class DataFrameRowSliceAdapter:
    """Tracks original dataframe and a boolean row mask
    
    This is a workaround to (1) save memory (2) keep id(row)
    consistent when iterating, as id() is used significantly
    by visidata's selectRow implementation.
    """
    def __init__(self, df, mask):
        import pandas as pd
        import numpy as np
        assert isinstance(df, pd.DataFrame)
        assert isinstance(mask, pd.Series) and df.shape[0] == mask.shape[0]
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

class PandasSheetFreqTable(SheetPivot):
    'Generate frequency-table sheet on currently selected column.'
    rowtype = 'bins'  # rowdef FreqRow(keys, sourcerows)

    def __init__(self, sheet, *groupByCols):
        fqcolname = '%s_%s_freq' % (sheet.name, '-'.join(col.name for col in groupByCols))
        super().__init__(fqcolname, groupByCols, [], source=sheet)
        self.largest = 1

    def selectRow(self, row):
        # raise ValueError(str(type(self.source)) + " " + str(type(row.sourcerows)))
        self.source.select(row.sourcerows)     # select all entries in the bin on the source sheet
        return super().selectRow(row)  # then select the bin itself on this sheet

    def unselectRow(self, row):
        self.source.unselect(row.sourcerows)
        return super().unselectRow(row)

    def updateLargest(self, grouprow):
        self.largest = max(self.largest, len(grouprow.sourcerows))

    @asyncthread
    def reload(self):
        'Generate frequency table then reverse-sort by length.'
        import pandas as pd

        # Conditions:
        # (2) this assumes some amount of non-degeneracy (non-empty dataframe with non-null values)
        # Note: visidata's base FrequencyTable bins numeric data in ranges (e.g. as a histogram).
        # We currently don't provide support for this for PandasSheet.
        super().initCols(use_range=False)
        # columns now the same as the original table
        # raise ValueError(str([c.name for c in self.columns]))

        df = self.source.rows
        
        if len(self.groupByCols) == 1:
            this_column = df.loc[:, str(self.groupByCols[0].name)]
            value_counts = this_column.value_counts()
        elif len(self.groupByCols) >= 1:
            this_column = df.loc[:, str(self.groupByCols[0].name)]
            # Compute cross-tabulation to get counts, and sort/remove zero-entries.
            # Note that this is not space-efficient: the initial cross-tabulation will
            # have space on the order of product of number of unique elements for each
            # column, even though its possible the combinations present are sparse
            # and most combinations have zero count.
            value_counts = pd.crosstab(this_column, [df.df[c.name] for c in self.groupByCols[1:]])
            value_counts = value_counts.stack(list(range(len(self.groupByCols) - 1)))
            value_counts = value_counts.loc[value_counts > 0].sort_values(ascending=False) 
        else:
            fail("Unable to do FrequencyTable, no columns to group on provided")

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

        # TODO: can make this part async w/ progress bar
        for element in Progress(value_counts.index):
            if len(self.groupByCols) == 1:
                element = (element,)
            assert len(element) == len(self.groupByCols)
            mask = df.df[self.groupByCols[0].name] == element[0]
            for i in range(1, len(self.groupByCols)):
                mask = mask & (df.df[self.groupByCols[i].name] == element[i])

            self.addRow(PivotGroupRow(
                element,
                (nankey, nankey),
                DataFrameRowSliceAdapter(df.df, mask),
                {}
            ))

        # if self.nCols > len(self.groupByCols)+3:  # hide percent/histogram if aggregations added
        #     self.column('percent').hide()
        #     self.column('histogram').hide()

PandasSheetFreqTable.addCommand('t', 'stoggle-row', 'toggle([cursorRow]); cursorDown(1)')
PandasSheetFreqTable.addCommand('s', 'select-row', 'select([cursorRow]); cursorDown(1)')
PandasSheetFreqTable.addCommand('u', 'unselect-row', 'unselect([cursorRow]); cursorDown(1)')

def expand_source_rows(source, vd, cursorRow):
    vs = copy(source)
    vs.name += "_" + valueNames(cursorRow.discrete_keys, cursorRow.numeric_key)
    if cursorRow.sourcerows is None:
        error("no source rows")
    vs.rows = cursorRow.sourcerows
    vd.push(vs)

# PandasSheetFreqTable.addCommand(ENTER, 'dup-row', 'vs = copy(source); vs.name += "_"+valueNames(cursorRow.discrete_keys, cursorRow.numeric_key); vs.rows=copy(cursorRow.sourcerows or error("no source rows")); vd.push(vs)')
PandasSheetFreqTable.addCommand(ENTER, 'dup-row', 'expand_source_rows(source, vd, cursorRow)')
