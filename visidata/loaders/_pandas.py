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
            filetype = getattr(self, 'filetype', self.source.ext[1:])
            if filetype == 'tsv':
                readfunc = self.read_tsv
            else:
                readfunc = getattr(pd, 'read_'+filetype) or error('no pandas.read_'+filetype)
            self.df = readfunc(self.source.resolve(), **options('pandas_'+filetype+'_'))

        # TODO: should we reset the index here and add it as a key column?
        self.columns = [
            ColumnItem(col, type=self.dtype_to_type(self.df[col]))
            for col in self.df.columns
            if not col.startswith("__vd_")  # reserved for internal usage
        ]

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
    def select(self, rows, status=True, progress=True):
        self._checkSelectedIndex()
        self._selectedMask.loc[[row.name for row in rows]] = True
    def unselect(self, rows, status=True, progress=True):
        self._checkSelectedIndex()
        self._selectedMask.loc[[row.name for row in rows]] = False
    def selectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask.iloc[start:end] = True

    def unselectByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask.iloc[start:end] = False

    def toggleByIndex(self, start=None, end=None):
        self._checkSelectedIndex()
        self._selectedMask.iloc[start:end] = ~self._selectedMask.iloc[start:end]

    def _selectByILoc(self, mask, selected=True):
        self._checkSelectedIndex()
        self._selectedMask.iloc[mask] = selected

def view_pandas(df):
    run(PandasSheet('', source=df))


def open_pandas(p):
    return PandasSheet(p.name, source=p)

def open_dta(p):
    return PandasSheet(p.name, source=p, filetype='stata')

open_stata = open_pandas

undoSheetSelection = undoAttrCopy('[sheet]', '_selectedMask')

# Override with vectorized implementations
PandasSheet.addCommand(None, 'stoggle-rows', 'toggleByIndex()', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'select-rows', 'selectByIndex()', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'unselect-rows', 'unselectByIndex()', undo=undoSheetSelection),

PandasSheet.addCommand(None, 'stoggle-before', 'toggleByIndex(end=cursorRowIndex)', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'select-before', 'selectByIndex(end=cursorRowIndex)', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'unselect-before', 'unselectByIndex(end=cursorRowIndex)', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'stoggle-after', 'toggleByIndex(start=cursorRowIndex)', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'select-after', 'selectByIndex(start=cursorRowIndex)', undo=undoSheetSelection),
PandasSheet.addCommand(None, 'unselect-after', 'unselectByIndex(start=cursorRowIndex)', undo=undoSheetSelection),
