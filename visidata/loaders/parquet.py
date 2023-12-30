from visidata import Sheet, VisiData, TypedWrapper, anytype, date, vlen, Column, vd
from collections import defaultdict


@VisiData.api
def open_parquet(vd, p):
    return ParquetSheet(p.base_stem, source=p)


class ParquetColumn(Column):
    def calcValue(self, row):
        val = self.source[row["__rownum__"]]
        if val.type == 'large_string':
            return memoryview(val.as_buffer())[:2**20].tobytes().decode('utf-8')
        else:
            return val.as_py()


class ParquetSheet(Sheet):
    # rowdef: {'__rownum__':int, parquet_col:overridden_value, ...}
    def iterload(self):
        pa = vd.importExternal("pyarrow", "pyarrow")
        pq = vd.importExternal("pyarrow.parquet", "pyarrow")
        from visidata.loaders.arrow import arrow_to_vdtype

        if self.source.is_dir():
            self.tbl = pq.read_table(str(self.source))
        else: 
            with self.source.open('rb') as f:
                self.tbl = pq.read_table(f)

        self.columns = []
        for colname, col in zip(self.tbl.column_names, self.tbl.columns):
            c = ParquetColumn(colname,
                              type=arrow_to_vdtype(col.type),
                              source=col,
                              cache=(col.type.id == pa.lib.Type_LARGE_STRING))
            self.addColumn(c)

        for i in range(self.tbl.num_rows):
            yield dict(__rownum__=i)


@VisiData.api
def save_parquet(vd, p, sheet):
    pa = vd.importExternal("pyarrow")
    pq = vd.importExternal("pyarrow.parquet", "pyarrow")

    typemap = {
        anytype: pa.string(),
        int: pa.int64(),
        vlen: pa.int64(),
        float: pa.float64(),
        str: pa.string(),
        date: pa.date64(),
        # list: pa.array(),
    }

    for t in vd.numericTypes:
        if t not in typemap:
            typemap[t] = pa.float64()

    databycol = defaultdict(list)  # col -> [values]

    for typedvals in sheet.iterdispvals(format=False):
        for col, val in typedvals.items():
            if isinstance(val, TypedWrapper):
                val = None

            databycol[col].append(val)

    data = [
        pa.array(vals, type=typemap.get(col.type, pa.string()))
        for col, vals in databycol.items()
    ]

    schema = pa.schema(
        [(c.name, typemap.get(c.type, pa.string())) for c in sheet.visibleCols]
    )
    with p.open_bytes(mode="w") as outf:
        with pq.ParquetWriter(outf, schema) as writer:
            writer.write_batch(
                pa.record_batch(data, names=[c.name for c in sheet.visibleCols])
            )
