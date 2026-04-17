import json

from visidata import Sheet, VisiData, TypedWrapper, anytype, date, vlen, Column, vd, asyncthread, Progress, InvertedCanvas
from collections import defaultdict


@VisiData.api
def open_parquet(vd, p):
    return ParquetSheet(p.base_stem, source=p)


class ParquetColumn(Column):
    @property
    def readonly(self) -> bool:
        return False

    def calcValue(self, row):
        if self.name in row:  #2890
            return row[self.name]
        rownum = row.get("__rownum__")
        if rownum is None:
            return None
        val = self.source[rownum]
        if val.type == 'large_string':
            return memoryview(val.as_buffer())[:2**20].tobytes().decode('utf-8')
        else:
            return val.as_py()

    def putValue(self, row, val):
        row[self.name] = val


class GeometryColumn(ParquetColumn):
    'Parquet column containing WKB-encoded geometries (GeoParquet).'
    @property
    def readonly(self) -> bool:
        return True

    def calcValue(self, row):
        val = super().calcValue(row)
        if val is None:
            return None
        return vd.importExternal('shapely').from_wkb(val)

    def formatValue(self, typedval, width=None):
        if typedval is None:
            return None
        shapely = vd.importExternal('shapely')
        n = shapely.get_num_coordinates(typedval)
        return f'{typedval.geom_type}[{n}]'


def _geoparquet_columns(schema):
    'Return set of column names that are WKB geometries per GeoParquet metadata.'
    names = set()
    meta = schema.metadata or {}
    geo = meta.get(b'geo')
    if geo:
        try:
            names.update(json.loads(geo).get('columns', {}).keys())
        except Exception as e:
            vd.exceptionCaught(e)
    # fallback: per-field ARROW extension marker
    for i in range(len(schema)):
        field = schema.field(i)
        fmd = field.metadata or {}
        if fmd.get(b'ARROW:extension:name') == b'geoarrow.wkb':
            names.add(field.name)
    return names


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

        geocols = _geoparquet_columns(self.tbl.schema)

        self.columns = []
        for colname, col in zip(self.tbl.column_names, self.tbl.columns):
            if colname in geocols:
                c = GeometryColumn(colname, type=anytype, source=col, cache=True)
            else:
                c = ParquetColumn(colname,
                                  type=arrow_to_vdtype(col.type),
                                  source=col,
                                  cache=(col.type.id == pa.lib.Type_LARGE_STRING))
            self.addColumn(c)

        for i in range(self.tbl.num_rows):
            yield dict(__rownum__=i)

    def geometryColumn(self):
        'Return first GeometryColumn on this sheet, or None.'
        for c in self.columns:
            if isinstance(c, GeometryColumn):
                return c
        return None


class ParquetGeoCanvas(InvertedCanvas):
    aspectRatio = 1.0

    @asyncthread
    def reload(self):
        self.reset()
        geocol = self.source.geometryColumn()
        if geocol is None:
            vd.warning('no geometry column')
            return
        for row in Progress(self.sourceRows):
            g = geocol.getTypedValue(row)
            if g is None:
                continue
            self._plot_geom(g, self.plotColor(self.source.rowkey(row)), row)
        self.refresh()

    def _plot_geom(self, g, attr, row):
        t = g.geom_type
        if t == 'Point':
            self.point(g.x, g.y, attr, row)
            disptext = self.textCol.getDisplayValue(row)
            if disptext:
                self.label(g.x, g.y, disptext, attr, row)
        elif t in ('LineString', 'LinearRing'):
            self.polyline(list(g.coords), attr, row)
        elif t == 'Polygon':
            self.polyline(list(g.exterior.coords), attr, row)
            for ring in g.interiors:
                self.polyline(list(ring.coords), attr, row)
        elif t in ('MultiPoint', 'MultiLineString', 'MultiPolygon', 'GeometryCollection'):
            for sub in g.geoms:
                self._plot_geom(sub, attr, row)
        else:
            vd.warning(f'unsupported geometry type `{t}`')


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


ParquetSheet.addCommand('.', 'plot-row', 'vd.push(ParquetGeoCanvas(name+"_map", source=sheet, sourceRows=[cursorRow], textCol=cursorCol))', 'plot geometry in current row')
ParquetSheet.addCommand('g.', 'plot-rows', 'vd.push(ParquetGeoCanvas(name+"_map", source=sheet, sourceRows=rows, textCol=cursorCol))', 'plot geometries in all rows')

vd.addGlobals(ParquetGeoCanvas=ParquetGeoCanvas)
