import json

from visidata import VisiData, vd, Sheet, Column, Progress, date, copy, InvertedCanvas, asyncthread

# requires pyshp


@VisiData.api
def open_shp(vd, p):
    return ShapeSheet(p.name, source=p)

VisiData.open_dbf = VisiData.open_shp

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

@VisiData.api
class ShapeMap(InvertedCanvas):
    aspectRatio = 1.0
    filetype = 'geojson'

    @asyncthread
    def reload(self):
        self.reset()

        for row in Progress(self.sourceRows):
            # color according to key
            k = self.source.rowkey(row)

            if row.shape.shapeType in (5, 15, 25):
                self.polygon(row.shape.points, self.plotColor(k), row)
            elif row.shape.shapeType in (3, 13, 23):
                self.polyline(row.shape.points, self.plotColor(k), row)
            elif row.shape.shapeType in (1, 11, 21):
                x, y = row.shape.points[0]
                self.point(x, y, self.plotColor(k), row)
            else:
                vd.status('notimpl shapeType %s' % row.shape.shapeType)

            x1, y1, x2, y2 = row.shape.bbox
            textx, texty = (x1+x2)/2, (y1+y2)/2
            disptext = self.textCol.getDisplayValue(row)
            self.label(textx, texty, disptext, self.plotColor(k), row)

        self.refresh()

@ShapeMap.api
def save_geojson(vd, p, vs):
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
    with p.open_text(mode='w', encoding=vs.options.encoding) as fp:
        for chunk in json.JSONEncoder().iterencode(featcoll):
            fp.write(chunk)

ShapeSheet.addCommand('.', 'plot-row', 'vd.push(ShapeMap(name+"_map", source=sheet, sourceRows=[cursorRow], textCol=cursorCol))', 'plot geospatial vector in current row')
ShapeSheet.addCommand('g.', 'plot-rows', 'vd.push(ShapeMap(name+"_map", source=sheet, sourceRows=rows, textCol=cursorCol))', 'plot all geospatial vectors in current sheet')
ShapeMap.addCommand('^S', 'save-sheet', 'vd.saveSheets(inputPath("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)', 'save current sheet to filename in format determined by extension (default .geojson)')
