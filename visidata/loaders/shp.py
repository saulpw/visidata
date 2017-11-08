
from visidata import *
import shapefile


def open_shp(p):
    return ShapeSheet(p.name, p)


def open_dbf(p):
    pass


class ShapeSheet(VectorCanvas):
    commands = VectorCanvas.commands + [
        Command('+', 'zoom(0.90)', 'zoom in'),
        Command('-', 'zoom(1.10)', 'zoom out'),
    ]

    @property
    def cursorBounds(self):
        'bounds of cursor in unit coords'
        return None

    def zoom(self, amt):
        w = self.unit_rightx - self.unit_leftx
        h = self.unit_bottomy - self.unit_topy
        w *= amt  # new w/h
        h *= amt

        # new center at cursor
        self.unit_leftx = self.cursorX - w/2
        self.unit_rightx = self.cursorX + w/2
        self.unit_topy = self.cursorY - h/2
        self.unit_bottomy = self.cursorY + h/2

    def reload(self):
        sf = shapefile.Reader(self.source.resolve())
        for shaperec in sf.iterShapeRecords():
            shape = shaperec.shape
            prev_x, prev_y = None, None
            for x, y in shape.points:
                if prev_x is None:
                    prev_x, prev_y = x, y
                else:
                    self.line(prev_x, prev_y, x, y, 'red')


