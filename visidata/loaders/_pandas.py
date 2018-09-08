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
        self.rows = DataFrameAdapter(self.source)
        self.columns = [ColumnItem(col) for col in self.source.columns]
