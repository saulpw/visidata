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

    def tilename(self, row):
        return ",".join(str(x) for x in row)

    def getTile(self, zoom_level, tile_col, tile_row):
        import mapbox_vector_tile

        con = sqlite3.connect(self.source.resolve())
        tile_data = con.execute('''
       SELECT tile_data FROM tiles
           WHERE zoom_level = ?
             AND tile_column = ?
             AND tile_row = ?''', (zoom_level, tile_col, tile_row)).fetchone()[0]

        return mapbox_vector_tile.decode(gzip.decompress(tile_data))

    @asyncthread
    def reload(self):
        con = sqlite3.connect(self.source.resolve())

        self.metadata = dict(con.execute('SELECT name, value FROM metadata').fetchall())

        tiles = con.execute('SELECT zoom_level, tile_column, tile_row FROM tiles')
        for r in Progress(tiles.fetchall()):
            self.addRow(r)


MbtilesSheet.addCommand(ENTER, 'dive-row', 'vd.push(PbfSheet(tilename(cursorRow), source=sheet, sourceRow=cursorRow))')
MbtilesSheet.addCommand('.', 'plot-row', 'tn=tilename(cursorRow); vd.push(PbfCanvas(tn+"_map", source=PbfSheet(tn, sourceRows=list(getFeatures(getTile(*cursorRow))))))')
#MbtilesSheet.addCommand('g.', '', 'tn=tilename(cursorRow); vd.push(PbfCanvas(tn+"_map", source=PbfSheet(tn), sourceRows=sum((list(getFeatures(getTile(*r))) for r in selectedRows or rows), [])))', 'plot selected tiles'),


class PbfSheet(Sheet):
    columns = [
        ColumnItem('layer', 0),
        Column('geometry_type', getter=lambda col,row: row[1]['geometry']['type']),
        Column('geometry_coords', getter=lambda col,row: row[1]['geometry']['coordinates'], width=0),
        Column('geometry_coords_depth', getter=lambda col,row: getListDepth(row[1]['geometry']['coordinates']), width=0),
    ]
    nKeys = 1  # layer
    @asyncthread
    def reload(self):
        props = set()  # property names
        self.rows = []
        for r in getFeatures(self.source.getTile(*self.sourceRow)):
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


PbfSheet.addCommand('.', 'plot-row', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=[cursorRow], textCol=cursorCol))')
PbfSheet.addCommand('g.', 'plot-selected', 'vd.push(PbfCanvas(name+"_map", source=sheet, sourceRows=selectedRows or rows, textCol=cursorCol))')
