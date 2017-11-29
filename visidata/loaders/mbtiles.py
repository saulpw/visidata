from visidata import *

import json
import gzip
import sqlite3

def open_pbf(p):
    return PbfSheet(p.name, tile_data=p.read_bytes())

def open_mbtiles(p):
    return MbtilesSheet(p.name, source=p)

def getListDepth(L):
    if not isinstance(L, list):
        return 0
    if len(L) == 0:
        return 0
    return getListDepth(L[0]) + 1

def getTile(con, zoom_level, tile_col, tile_row):
    import mapbox_vector_tile

    tile_data = con.execute('''
       SELECT tile_data FROM tiles
           WHERE zoom_level = ?
             AND tile_column = ?
             AND tile_row = ?''', (zoom_level, tile_col, tile_row)).fetchone()[0]

    return mapbox_vector_tile.decode(gzip.decompress(tile_data))

def getFeatures(tile_data):
    for layername, layer in tile_data.items():
        for feat in layer['features']:
            yield layername, feat


class MbtilesSheet(Sheet):
    columns = [
        ColumnItem('zoom_level', 0),
        ColumnItem('tile_column', 1),
        ColumnItem('tile_row', 2),
    ]

    commands = [
        Command(ENTER, 'vd.push(PbfSheet(tilename(cursorRow)+"_foo", tile_data=getTile(con, *cursorRow)))', 'view this tile'),
        Command('.', 'vd.push(PbfCanvas(tilename(cursorRow)+"_map", source=PbfSheet("foo"), sourceRows=list(getFeatures(getTile(con, *cursorRow)))))', 'view this tile'),
        Command('g.', 'vd.push(PbfCanvas(tilename(cursorRow)+"_map", source=PbfSheet("foo"), sourceRows=sum((list(getFeatures(getTile(sheet.con, *r))) for r in selectedRows or rows), [])))', 'view selected tiles'),
#        Command('1', 'vd.push(load_pyobj("foo", getTile(con, *cursorRow)))', 'push raw data for this tile'),
    ]

    def tilename(self, row):
        return ",".join(str(x) for x in row)

    def reload(self):
        self.con = sqlite3.connect(self.source.resolve())

        self.metadata = dict(self.con.execute('SELECT name, value FROM metadata').fetchall())

        tiles = self.con.execute('SELECT zoom_level, tile_column, tile_row FROM tiles')
        self.rows = tiles.fetchall()


class PbfSheet(Sheet):
    columns = [
        ColumnItem('layer', 0),
        Column('geometry_type', getter=lambda col,row: row[1]['geometry']['type']),
        Column('geometry_coords', getter=lambda col,row: row[1]['geometry']['coordinates']),
        Column('geometry_coords_depth', getter=lambda col,row: getListDepth(row[1]['geometry']['coordinates'])),
    ]
    nKeys = 1  # layer
    commands = [
        Command('.', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=[cursorRow]))', 'plot this row only'),
        Command('g.', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=selectedRows or rows))', 'plot as map'),
    ]
    @async
    def reload(self):
        props = set()  # property names
        self.rows = []
        for r in getFeatures(self.tile_data):
            self.rows.append(r)
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
            assert False, t

    @async
    def reload(self):
        self.reset()

        for r in Progress(self.sourceRows):
            for vertexes, attr, row in self.iterpolylines(r):
                self.polyline(vertexes, attr, row)

        self.refresh()
