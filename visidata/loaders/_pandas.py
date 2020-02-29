from visidata import *


class DataFrameAdapter:

    def __init__(self, df):
        import pandas as pd
        assert isinstance(df, pd.DataFrame)
        self.df = df

    def __len__(self):
        return len(self.df)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return DataFrameAdapter(self.df.iloc[k])
        return self.df.iloc[k]

    def __getattr__(self, k):
        return getattr(self.df, k)


# source=DataFrame
class PandasSheet(Sheet):
    '''Sheet sourced from a pandas.DataFrame

    Warning:
        The index of the pandas.DataFrame input must be unique.
        Otherwise the selection functionality, which relies on
        looking up selected rows via the index, will break.
        This can be done by calling reset_index().

    Note:
        Columns starting with "__vd_" are reserved for internal usage
        by the VisiData loader.
    '''

    def dtype_to_type(self, dtype):
        import numpy as np
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

    def read_tsv(self, path, **kwargs):
        'Partial function for reading TSV files using pd.read_csv'
        import pandas as pd
        return pd.read_csv(path, sep='\t', **kwargs)

    def reload(self):
        import pandas as pd
        if isinstance(self.source, pd.DataFrame):
            self.df = self.source
        elif isinstance(self.source, Path):
            filetype = getattr(self, 'filetype', self.source.ext)
            if filetype == 'tsv':
                readfunc = self.read_tsv
            else:
                readfunc = getattr(pd, 'read_'+filetype) or error('no pandas.read_'+filetype)
            self.df = readfunc(str(self.source), **options('pandas_'+filetype+'_'))

        # reset the index here
        if type(self.df.index) is not pd.RangeIndex:
            self.df = self.df.reset_index()

        self.columns = [
            ColumnItem(col, type=self.dtype_to_type(self.df[col]))
            for col in self.df.columns
            if not col.startswith("__vd_")  # reserved for internal usage
        ]

        if self.columns[0].name == 'index': # if the df contains an index column
            self.column('index').hide()


        self.rows = DataFrameAdapter(self.df)
        self._selectedMask = pd.Series(False, index=self.df.index)
        if self.df.index.nunique() != self.df.shape[0]:
            warning("Non-unique index, row selection API may not work or may be incorrect")

    @asyncthread
    def sort(self):
        'Sort rows according to the current self._ordering.'
        by_cols = []
        ascending = []
        for cols, reverse in self._ordering[::-1]:
            by_cols += [col.name for col in cols]
            ascending += [not reverse] * len(cols)
        self.rows.sort_values(by=by_cols, ascending=ascending, inplace=True)

    def _checkSelectedIndex(self):
        import pandas as pd
        if self._selectedMask.index is not self.df.index:
            # self.df was modified inplace, so the selection is no longer valid
            vd.status('pd.DataFrame.index updated, clearing {} selected rows'
                      .format(self._selectedMask.sum()))
            self._selectedMask = pd.Series(False, index=self.df.index)

    def rowid(self, row):
        return row.name

    # Base selection API. Refer to GH #266: using id() will not identify
    # pandas rows since iterating on rows / selecting rows will return
    # different copies. Instead, re-implement the selection API by
    # keeping a boolean pd.Series indicating the selected rows.
    def isSelected(self, row):
        if row is None:
            return False
        self._checkSelectedIndex()
        return self._selectedMask.loc[row.name]

    def selectRow(self, row):
        'Select given row'
        self._checkSelectedIndex()
        self._selectedMask.loc[row.name] = True

    def unselectRow(self, row):
        self._checkSelectedIndex()
        is_selected = self._selectedMask.loc[row.name]
        self._selectedMask.loc[row.name] = False
        return is_selected

    @property
    def nSelected(self):
        self._checkSelectedIndex()
        return self._selectedMask.sum()

    @property
    def selectedRows(self):
        self._checkSelectedIndex()
        return DataFrameAdapter(self.df.loc[self._selectedMask])

    # Vectorized implementation of multi-row selections
    @asyncthread
    def select(self, rows, status=True, progress=True):
        self.addUndoSelection()
        for row in (Progress(rows, 'selecting') if progress else rows):
            self.selectRow(row)

    @asyncthread
    def unselect(self, rows, status=True, progress=True):
        self.addUndoSelection()
        for row in (Progress(rows, 'unselecting') if progress else rows):
            select.unselectRow(row)

    def clearSelected(self):
        self._selectedMask = pd.Series(False, index=self.df.index)

    def selectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask.iloc[start:end] = True

    def unselectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask.iloc[start:end] = False

    def toggleByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self.addUndoSelection()
        self._selectedMask.iloc[start:end] = ~self._selectedMask.iloc[start:end]

    def _selectByILoc(self, mask, selected=True):
        self._checkSelectedIndex()
        self._selectedMask.iloc[mask] = selected

    def addUndoSelection(self):
        self.addUndo(undoAttrCopyFunc([self], '_selectedMask'))

def view_pandas(df):
    run(PandasSheet('', source=df))


def open_pandas(p):
    return PandasSheet(p.name, source=p)

def open_dta(p):
    return PandasSheet(p.name, source=p, filetype='stata')

open_stata = open_pandas

# Override with vectorized implementations
PandasSheet.addCommand(None, 'stoggle-rows', 'toggleByIndex()')
PandasSheet.addCommand(None, 'select-rows', 'selectByIndex()')
PandasSheet.addCommand(None, 'unselect-rows', 'unselectByIndex()')

PandasSheet.addCommand(None, 'stoggle-before', 'toggleByIndex(end=cursorRowIndex)')
PandasSheet.addCommand(None, 'select-before', 'selectByIndex(end=cursorRowIndex)')
PandasSheet.addCommand(None, 'unselect-before', 'unselectByIndex(end=cursorRowIndex)')
PandasSheet.addCommand(None, 'stoggle-after', 'toggleByIndex(start=cursorRowIndex)')
PandasSheet.addCommand(None, 'select-after', 'selectByIndex(start=cursorRowIndex)')
PandasSheet.addCommand(None, 'unselect-after', 'unselectByIndex(start=cursorRowIndex)')
PandasSheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=DataFrameAdapter(sheet.df.sample(nrows or nRows)); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows'),
