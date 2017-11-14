
from visidata import *
import shapefile


def open_shp(p):
    return ShapeSheet(p.name, p)


def open_dbf(p):
    pass


class ShapeSheet(GridCanvas):
    aspectRatio = 1.0

    @async
    def reload(self):
        attr = colors['blue']
        sf = shapefile.Reader(self.source.resolve())
        self.gridlines.clear()

        for shaperec in sf.iterShapeRecords():
            shape = shaperec.shape
            prev_x, prev_y = None, None
            for x, y in shape.points:
                if prev_x is not None:
                    self.line(prev_x, prev_y, x, y, attr)
                prev_x, prev_y = x, y

        self.refresh()
