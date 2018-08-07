from visidata import *


def open_shp(p):
    return ShapeSheet(p.name, source=p)

# pyshp doesn't care about file extensions
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
    @asyncthread
    def reload(self):
        import shapefile
        sf = shapefile.Reader(self.source.resolve())
        for i, (fname, ftype, fieldlen, declen) in enumerate(sf.fields[1:]):  # skip DeletionFlag
            self.addColumn(Column(fname, getter=lambda col,row,i=i: row.record[i], type=shptype(ftype, declen)))
        self.rows = []
        for shaperec in Progress(sf.iterShapeRecords(), total=sf.numRecords):
            self.addRow(shaperec)

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
                status('notimpl shapeType %s' % row.shape.shapeType)

            x1, y1, x2, y2 = row.shape.bbox
            textx, texty = (x1+x2)/2, (y1+y2)/2
            disptext = self.textCol.getDisplayValue(row)
            self.label(textx, texty, disptext, self.plotColor(k), row)

        self.refresh()

ShapeSheet.addCommand('.', 'plot-row', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=[cursorRow], textCol=cursorCol))')
ShapeSheet.addCommand('g.', 'plot-selected', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=selectedRows or rows, textCol=cursorCol))')
ShapeMap.addCommand('^S', 'save-geojson', 'save_geojson(Path(input("json to save: ", value=name+".geojson")), sheet)')


def save_geojson(p, vs):
    assert isinstance(vs, Canvas), 'need Canvas to save geojson'

    features = []
    for coords, attr, row in Progress(vs.polylines):
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
