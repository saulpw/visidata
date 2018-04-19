from visidata import *


def open_dta(p):
    return StataSheet(p.name, source=p)


class StataSheet(Sheet):
    @async
    def reload(self):
        import pandas
        self.df = pandas.read_stata(self.source.resolve())
        self.columns = [Column(cname, getter=lambda col,row,i=i: row.iloc[i]) for i, cname in enumerate(self.df.columns)]
        self.rows = []
        for i, r in Progress(self.df.iterrows(), total=self.df.shape[0]):
            self.rows.append(r)
