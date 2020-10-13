from functools import partial

from visidata import *

def open_pandas(p):
    return PandasSheet(p.name, source=p)

def open_dta(p):
    return PandasSheet(p.name, source=p, filetype='stata')

open_stata = open_pandas

for ft in 'feather gbq orc parquet pickle sas stata'.split():
    globals().setdefault('open_'+ft, lambda p,ft=ft: PandasSheet(p.name, source=p, filetype=ft))

class DataFrameAdapter:

    def __init__(self, df):
        import pandas as pd
        assert isinstance(df, pd.DataFrame)
        self.df = df

    def __len__(self):
        if 'df' not in self.__dict__:
            return 0
        return len(self.df)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return DataFrameAdapter(self.df.iloc[k])
        return self.df.iloc[k]

    def __getattr__(self, k):
        if 'df' not in self.__dict__:
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{k}'")
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

    def read_tsv(self, path, **kwargs):
        'Partial function for reading TSV files using pd.read_csv'
        import pandas as pd
        return pd.read_csv(path, sep='\t', **kwargs)

    @property
    def df(self):
        if isinstance(getattr(self, 'rows', None), DataFrameAdapter):
            return self.rows.df

    @df.setter
    def df(self, val):
        if isinstance(getattr(self, 'rows', None), DataFrameAdapter):
            self.rows.df = val
        else:
            self.rows = DataFrameAdapter(val)

    def getValue(self, col, row):
        '''Look up column values in the underlying DataFrame.'''
        return col.sheet.df.loc[row.name, col.name]

    def setValue(self, col, row, val):
        '''
        Update a column's value in the underlying DataFrame, loosening the
        column's type as needed. Take care to avoid assigning to a view or
        a copy as noted here:

        https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#why-does-assignment-fail-when-using-chained-indexing
        '''
        try:
            col.sheet.df.loc[row.name, col.name] = val
        except ValueError as err:
            vd.warning(f'Type of {val} does not match column {col.name}. Changing type.')
            col.type = anytype
            col.sheet.df.loc[row.name, col.name] = val

    def reload(self):
        import pandas as pd
        if isinstance(self.source, pd.DataFrame):
            df = self.source
        elif isinstance(self.source, Path):
            filetype = getattr(self, 'filetype', self.source.ext)
            if filetype == 'tsv':
                readfunc = self.read_tsv
            elif filetype == 'jsonl':
                readfunc = partial(pd.read_json, lines=True)
            else:
                readfunc = getattr(pd, 'read_'+filetype) or vd.error('no pandas.read_'+filetype)
            df = readfunc(str(self.source), **options.getall('pandas_'+filetype+'_'))

        # reset the index here
        if type(df.index) is not pd.RangeIndex:
            df = df.reset_index()

        self.columns = []
        for col in (c for c in df.columns if not c.startswith("__vd_")):
            self.addColumn(Column(
                col,
                type=self.dtype_to_type(df[col]),
                getter=self.getValue,
                setter=self.setValue
            ))

        if self.columns[0].name == 'index': # if the df contains an index column
            self.column('index').hide()

        self.rows = DataFrameAdapter(df)
        self._selectedMask = pd.Series(False, index=df.index)
        if df.index.nunique() != df.shape[0]:
            vd.warning("Non-unique index, row selection API may not work or may be incorrect")

    @asyncthread
    def sort(self):
        '''Sort rows according to the current self._ordering.'''
        by_cols = []
        ascending = []
        for col, reverse in self._ordering[::-1]:
            by_cols.append(col.name)
            ascending.append(not reverse)
        self.rows.sort_values(by=by_cols, ascending=ascending, inplace=True)

    def _checkSelectedIndex(self):
        import pandas as pd
        if self._selectedMask.index is not self.df.index:
            # DataFrame was modified inplace, so the selection is no longer valid
            vd.status('pd.DataFrame.index updated, clearing {} selected rows'
                      .format(self._selectedMask.sum()))
            self._selectedMask = pd.Series(False, index=self.df.index)

    def rowid(self, row):
        return getattr(row, 'name', None) or ''

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
            self.unselectRow(row)

    def clearSelected(self):
        import pandas as pd
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

    @asyncthread
    def selectByRegex(self, regex, columns, unselect=False):
        '''
        Find rows matching regex in the provided columns. By default, add
        matching rows to the selection. If unselect is True, remove from the
        active selection instead.
        '''
        import pandas as pd
        case_sensitive = 'I' not in vd.options.regex_flags
        masks = pd.DataFrame([
            self.df[col.name].astype(str).str.contains(pat=regex, case=case_sensitive, regex=True)
            for col in columns
        ])
        if unselect:
            self._selectedMask = self._selectedMask & ~masks.any()
        else:
            self._selectedMask = self._selectedMask | masks.any()

    def addUndoSelection(self):
        vd.addUndo(undoAttrCopyFunc([self], '_selectedMask'))

    @property
    def nRows(self):
        if self.df is None:
            return 0
        return len(self.df)

    def newRows(self, n):
        '''
        Return n rows of empty data. Let pandas decide on the most
        appropriate missing value (NaN, NA, etc) based on the underlying
        DataFrame's dtypes.
        '''

        import pandas as pd
        return pd.DataFrame({
            col: [None] * n for col in self.df.columns
        }).astype(self.df.dtypes.to_dict(), errors='ignore')

    def _addRows(self, rows, idx):
        import pandas as pd
        if idx is None:
            self.df = self.df.append(pd.DataFrame(rows))
        else:
            self.df = pd.concat((self.df.iloc[0:idx], pd.DataFrame(rows), self.df.iloc[idx:]))
        self.df.index = pd.RangeIndex(self.nRows)
        self._checkSelectedIndex()

    def _deleteRows(self, which):
        import pandas as pd
        self.df.drop(which, inplace=True)
        self.df.index = pd.RangeIndex(self.nRows)
        self._checkSelectedIndex()

    def addNewRows(self, n, idx=None):
        self._addRows(self.newRows(n), idx)
        idx = idx or self.nRows - 1
        vd.addUndo(self._deleteRows, range(idx, idx + n))

    def addRow(self, row, idx=None):
        self._addRows([row], idx)
        vd.addUndo(self._deleteRows, idx or self.nRows - 1)

    def delete_row(self, rowidx):
        import pandas as pd
        oldrow = self.df.iloc[rowidx:rowidx+1]

        # Use to_dict() here to work around an edge case when applying undos.
        # As an action is undone, its entry gets removed from the cmdlog sheet.
        # If we use `oldrow` directly, we get errors comparing DataFrame objects
        # when there are multiple deletion commands for the same row index.
        # There may be a better way to handle that case.
        vd.addUndo(self._addRows, oldrow.to_dict(), rowidx)
        self._deleteRows(rowidx)
        vd.cliprows = [(self, rowidx, oldrow)]

    def deleteBy(self, by):
        '''Delete rows for which func(row) is true.  Returns number of deleted rows.'''
        import pandas as pd
        oldidx = self.cursorRowIndex
        nRows = self.nRows
        vd.addUndo(setattr, self, 'df', self.df.copy())
        self.df = self.df[~by]
        self.df.index = pd.RangeIndex(self.nRows)
        ndeleted = nRows - self.nRows

        vd.status('deleted %s %s' % (ndeleted, self.rowtype))
        return ndeleted

    def deleteSelected(self):
        '''Delete all selected rows.'''
        self.deleteBy(self._selectedMask)

def view_pandas(df):
    run(PandasSheet('', source=df))


# Override with vectorized implementations
PandasSheet.addCommand(None, 'stoggle-rows', 'toggleByIndex()', 'toggle selection of all rows')
PandasSheet.addCommand(None, 'select-rows', 'selectByIndex()', 'select all rows')
PandasSheet.addCommand(None, 'unselect-rows', 'unselectByIndex()', 'unselect all rows')

PandasSheet.addCommand(None, 'stoggle-before', 'toggleByIndex(end=cursorRowIndex)', 'toggle selection of rows from top to cursor')
PandasSheet.addCommand(None, 'select-before', 'selectByIndex(end=cursorRowIndex)', 'select all rows from top to cursor')
PandasSheet.addCommand(None, 'unselect-before', 'unselectByIndex(end=cursorRowIndex)', 'unselect all rows from top to cursor')
PandasSheet.addCommand(None, 'stoggle-after', 'toggleByIndex(start=cursorRowIndex)', 'toggle selection of rows from cursor to bottom')
PandasSheet.addCommand(None, 'select-after', 'selectByIndex(start=cursorRowIndex)', 'select all rows from cursor to bottom')
PandasSheet.addCommand(None, 'unselect-after', 'unselectByIndex(start=cursorRowIndex)', 'unselect all rows from cursor to bottom')
PandasSheet.addCommand(None, 'random-rows', 'nrows=int(input("random number to select: ", value=nRows)); vs=copy(sheet); vs.name=name+"_sample"; vs.rows=DataFrameAdapter(sheet.df.sample(nrows or nRows)); vd.push(vs)', 'open duplicate sheet with a random population subset of N rows'),

# Handle the regex selection family of commands through a single method,
# since the core logic is shared
PandasSheet.addCommand('|', 'select-col-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=[cursorCol])', 'select rows matching regex in current column')
PandasSheet.addCommand('\\', 'unselect-col-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=[cursorCol], unselect=True)', 'unselect rows matching regex in current column')
PandasSheet.addCommand('g|', 'select-cols-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=visibleCols)', 'select rows matching regex in any visible column')
PandasSheet.addCommand('g\\', 'unselect-cols-regex', 'selectByRegex(regex=input("select regex: ", type="regex", defaultLast=True), columns=visibleCols, unselect=True)', 'unselect rows matching regex in any visible column')
