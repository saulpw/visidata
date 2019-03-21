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
            return DataFrameAdapter(self.df[k])
        return self.df.iloc[k]

    def __getattr__(self, k):
        return getattr(self.df, k)


# source=DataFrame
class PandasSheet(Sheet):
    def dtype_to_type(self, dtype):
        import numpy as np
        try:
            if np.issubdtype(dtype, np.int):
                return int 
            if np.issubdtype(dtype, np.float):
              return float
            if np.issubdtype(dtype, np.datetime64):
                return date
        except TypeError:
            # For categoricals and other pandas-defined dtypes
            pass
        return anytype
   
    def read_tsv(self, path, **kwargs):
        """Partial function for reading TSV files using pd.read_csv"""
        import pandas as pd
        return pd.read_csv(path, sep='\t', **kwargs)

    # @property
    # def selectedRows(self):
    #     if len(self._selectedRows) <= 1:
    #         return list(self._selectedRows.values())
    #     return [self.rows.iloc[i] for i in range(self.rows.shape[0]) if id(self.rows.iloc[i]) in self._selectedRows]

    # def selectRow(self, row):
    #     super().selectRow(row)
    #     raise ValueError(self.selectedRows)

    def reload(self):
        import pandas
        if isinstance(self.source, pandas.DataFrame):
            self.df = self.source
        elif isinstance(self.source, Path):
            filetype = getattr(self, 'filetype', self.source.ext[1:])
            if filetype == 'tsv':
                readfunc = self.read_tsv 
            else:
                readfunc = getattr(pandas, 'read_'+filetype) or error('no pandas.read_'+filetype)
            self.df = readfunc(self.source.resolve(), **options('pandas_'+filetype+'_'))

        self.columns = [ColumnItem(col, type=self.dtype_to_type(self.df[col])) for col in self.df.columns]
        self.rows = DataFrameAdapter(self.df)

    @asyncthread
    def sort(self):
        'Sort rows according to the current self._ordering.'
        by_cols = []
        ascending = []
        for cols, reverse in self._ordering[::-1]:
            by_cols += [col.name for col in cols]
            ascending += [not reverse] * len(cols)
        self.rows.sort_values(by=by_cols, ascending=ascending, inplace=True)


def view_pandas(df):
    run(PandasSheet('', source=df))


def open_pandas(p):
    return PandasSheet(p.name, source=p)

def open_dta(p):
    return PandasSheet(p.name, source=p, filetype='stata')

open_stata = open_pandas
