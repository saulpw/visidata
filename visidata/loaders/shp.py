from visidata import *

# requires pyshp


def open_shp(p):
    return ShapeSheet(p.name, source=p)

open_dbf = open_shp

shptypes = {
  'C': str,
  'N': float,
  'L': float,
  'F': float,
  'D': date,
  'M': str,
}

def shptype(ftype, declen):
    t = shptypes[ftype[:1]]
    if t is float and declen == 0:
        return int
    return t

# rowdef: shaperec
class ShapeSheet(Sheet):
    rowtype = 'shapes'
    columns = [
        Column('shapeType', width=0, getter=lambda col,row: row.shape.shapeType)
    ]
    def iterload(self):
        import shapefile
        self.sf = shapefile.Reader(str(self.source))
        self.reloadCols()
        for shaperec in Progress(self.sf.iterShapeRecords(), total=self.sf.numRecords):
            yield shaperec

    def reloadCols(self):
        self.columns = []
        for c in ShapeSheet.columns:
            self.addColumn(copy(c))

        for i, (fname, ftype, fieldlen, declen) in enumerate(self.sf.fields[1:]):  # skip DeletionFlag
            self.addColumn(Column(fname, getter=lambda col,row,i=i: row.record[i], type=shptype(ftype, declen)))

class ShapeMap(InvertedCanvas):
    aspectRatio = 1.0
    @asyncthread
    def reload(self):
        self.reset()

        for row in Progress(self.sourceRows):
            # color according to key
            k = tuple(col.getValue(row) for col in self.source.keyCols)

            if row.shape.shapeType == 5:
                self.polygon(row.shape.points, self.plotColor(k), row)
            elif row.shape.shapeType == 3:
                self.polyline(row.shape.points, self.plotColor(k), row)
            elif row.shape.shapeType == 1:
                x, y = row.shape.points[0]
                self.point(x, y, self.plotColor(k), row)
            else:
                vd.status('notimpl shapeType %s' % row.shape.shapeType)

            x1, y1, x2, y2 = row.shape.bbox
            textx, texty = (x1+x2)/2, (y1+y2)/2
            disptext = self.textCol.getDisplayValue(row)
            self.label(textx, texty, disptext, self.plotColor(k), row)

        self.refresh()

@VisiData.api
def save_geojson(vd, p, vs):
    isinstance(vs, Canvas) or vd.fail("must save geojson from canvas sheet")
    features = []
    for coords, attr, row in Progress(vs.polylines, 'saving'):
        feat = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[x, y] for x, y in coords],
            },
            'properties': {
                col.name: col.getTypedValue(row) for col in vs.source.visibleCols
            }
        }
        features.append(feat)

    featcoll = {
        'type': 'FeatureCollection',
        'features': features,
    }
    with p.open_text(mode='w') as fp:
        for chunk in json.JSONEncoder().iterencode(featcoll):
            fp.write(chunk)

ShapeSheet.addCommand('.', 'plot-row', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=[cursorRow], textCol=cursorCol))', 'plot geospatial vector in current row')
ShapeSheet.addCommand('g.', 'plot-rows', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=rows, textCol=cursorCol))', 'plot all geospatial vectors in current sheet')
