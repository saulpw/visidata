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
    commands = [
        Command('.', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=[cursorRow], textCol=cursorCol))', ''),
        Command('g.', 'vd.push(ShapeMap(name+"_map", sheet, sourceRows=selectedRows or rows, textCol=cursorCol))', ''),
    ]
    @async
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

    @async
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
