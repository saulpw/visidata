from visidata import VisiData, vd, Sheet, Column, asyncthread, Progress, ColumnItem, InvertedCanvas

import gzip
import sqlite3

@VisiData.api
def open_pbf(vd, p):
    return PbfSheet(p.name, source=p)

@VisiData.api
def open_mbtiles(vd, p):
    return MbtilesSheet(p.name, source=p)

def getListDepth(L):
    if not isinstance(L, list):
        return 0
    if len(L) == 0:
        return 0
    return getListDepth(L[0]) + 1

def getFeatures(tile_data):
    for layername, layer in tile_data.items():
        for feat in layer['features']:
            yield layername, feat


def tilename(row):
    return ",".join(str(x) for x in row)


class MbtilesSheet(Sheet):
    columns = [
        ColumnItem('zoom_level', 0),
        ColumnItem('tile_column', 1),
        ColumnItem('tile_row', 2),
    ]

    def getTile(self, zoom_level, tile_col, tile_row):
        import mapbox_vector_tile

        con = sqlite3.connect(str(self.source))
        tile_data = con.execute('''
       SELECT tile_data FROM tiles
           WHERE zoom_level = ?
             AND tile_column = ?
             AND tile_row = ?''', (zoom_level, tile_col, tile_row)).fetchone()[0]

        return mapbox_vector_tile.decode(gzip.decompress(tile_data))

    def iterload(self):
        con = sqlite3.connect(str(self.source))

        self.metadata = dict(con.execute('SELECT name, value FROM metadata').fetchall())

        tiles = con.execute('SELECT zoom_level, tile_column, tile_row FROM tiles')
        yield from Progress(tiles.fetchall())

    def getPlot(self, *rows):
        if len(rows) == 1:
            name = self.name+'_'+tilename(rows[0])
        else:
            name = self.name+'_selected'

        sourceRows = sum((list(getFeatures(self.getTile(*r))) for r in rows), [])
        return PbfCanvas(name+"_map", source=PbfSheet(name, source=self), sourceRows=sourceRows)

    def openRow(self, row):
        'load table referenced in current row into memory'
        return PbfSheet(tilename(row), source=self, sourceRow=row)


class PbfSheet(Sheet):
    columns = [
        ColumnItem('layer', 0),
        Column('geometry_type', getter=lambda col,row: row[1]['geometry']['type']),
        Column('geometry_coords', getter=lambda col,row: row[1]['geometry']['coordinates'], width=0),
        Column('geometry_coords_depth', getter=lambda col,row: getListDepth(row[1]['geometry']['coordinates']), width=0),
    ]
    nKeys = 1  # layer

    def iterload(self):
        props = set()  # property names
        for r in getFeatures(self.source.getTile(*self.sourceRow)):
            yield r
            props.update(r[1]['properties'].keys())

        for key in props:
            self.addColumn(Column(key, getter=lambda col,row,key=key: row[1]['properties'][key]))


class PbfCanvas(InvertedCanvas):
    aspectRatio = 1.0
    def iterpolylines(self, r):
        layername, feat = r
        geom = feat['geometry']
        t = geom['type']
        coords = geom['coordinates']
        key = self.source.rowkey(r)

        if t == 'LineString':
            yield coords, self.plotColor(key), r
        elif t == 'Point':
            yield [coords], self.plotColor(key), r
        elif t == 'Polygon':
            for poly in coords:
                yield poly+[poly[0]], self.plotColor(key), r
        elif t == 'MultiLineString':
            for line in coords:
                yield line, self.plotColor(key), r
        elif t == 'MultiPolygon':
            for mpoly in coords:
                for poly in mpoly:
                    yield poly+[poly[0]], self.plotColor(key), r
        else:
            vd.warning('unknown geometry type %s' % t)

    @asyncthread
    def reload(self):
        self.reset()

        for r in Progress(self.sourceRows):
            for vertexes, attr, row in self.iterpolylines(r):
                self.polyline(vertexes, attr, row)

                if len(vertexes) == 1:
                    textx, texty = vertexes[0]
                    disptext = self.textCol.getDisplayValue(row)
                    if disptext:
                        self.label(textx, texty, disptext, attr, row)


        self.refresh()


PbfSheet.addCommand('.', 'plot-row', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=[cursorRow], textCol=cursorCol))', 'plot blocks in current row')
PbfSheet.addCommand('g.', 'plot-rows', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=rows, textCol=cursorCol))', 'plot selected blocks')
MbtilesSheet.addCommand('.', 'plot-row', 'vd.push(getPlot(cursorRow))', 'plot tiles in current row')
MbtilesSheet.addCommand('g.', 'plot-selected', 'vd.push(getPlot(*selectedRows))', 'plot selected tiles'),
