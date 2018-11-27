from visidata import *


class DataFrameAdapter:
    def __init__(self, df):
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
    def reload(self):
        import pandas
        import numpy
        def dtypeToType(df, colname):
            t = df[colname].dtype
            if t == numpy.int64: return int
            if t == numpy.float64: return float
#            if t == pandas.Timestamp: return date
            return anytype

        if isinstance(self.source, pandas.DataFrame):
            self.df = self.source
        elif isinstance(self.source, Path):
            filetype = getattr(self, 'filetype', self.source.ext[1:])
            readfunc = getattr(pandas, 'read_'+filetype) or error('no pandas.read_'+filetype)
            self.df = readfunc(self.source.resolve(), **options('pandas_'+filetype+'_'))

        self.columns = [ColumnItem(col, type=dtypeToType(self.df, col)) for col in self.df.columns]
        self.rows = DataFrameAdapter(self.df)


def view_pandas(df):
    run(PandasSheet('', source=df))


def open_pandas(p):
    return PandasSheet(p.name, source=p)

def open_dta(p):
    return PandasSheet(p.name, source=p, filetype='stata')

open_stata = open_pandas
