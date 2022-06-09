from visidata import VisiData, Sheet, Column


@VisiData.api
def open_parquet(vd, p):
    return ParquetSheet(p.name, source=p)

class ParquetColumn(Column):
    def calcValue(self, row):
        return self.source[row['__rownum__']].as_py()


class ParquetSheet(Sheet):
    # rowdef: {'__rownum__':int, parquet_col:overridden_value, ...}
    def iterload(self):
        import pyarrow.parquet as pq
        from visidata.loaders.arrow import arrow_to_vdtype

        self.tbl = pq.read_table(self.source)
        self.columns = []
        for colname, col in zip(self.tbl.column_names, self.tbl.columns):
            c = ParquetColumn(colname,
                              type=arrow_to_vdtype(col.type),
                              source=col)
            self.addColumn(c)

        for i in range(self.tbl.num_rows):
            yield dict(__rownum__=i)
