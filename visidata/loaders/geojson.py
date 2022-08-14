from functools import reduce
import json

from visidata import VisiData, vd, Column, asyncthread, Progress, PythonSheet, InvertedCanvas, deepcopy, date, wrapply, TypedExceptionWrapper, TypedWrapper


@VisiData.api
def open_geojson(vd, p):
    return GeoJSONSheet(p.name, source=p)

class GeoJSONColumn(Column):
    def calcValue(self, row):
        return row.get('properties', {}).get(self.expr)

    def putValue(self, row, val):
        properties = row.setdefault('properties', {})
        properties[self.expr] = val

class GeoJSONSheet(PythonSheet):
    rowtype = 'shapes'

    def iterload(self):
        self.colnames = {}
        self.columns = [Column('json_row', width=0)]

        with self.source.open_text(encoding='utf-8') as fp:
            ret = json.load(fp)

            if ret['type'] == 'FeatureCollection':
                features = ret['features']
            elif ret['type'] == 'Feature':
                features = [ret]
            elif ret['type'] == 'GeometryCollection':
                features = list(map(lambda g: { 'type': 'Feature', 'geometry': g }, ret['geometries']))
            else: # Some form of geometry
                features = [{ 'type': 'Feature', 'geometry': ret }]

            for feature in Progress(features):
                for prop in feature.get('properties', {}).keys():
                    prop = self.maybeClean(prop)
                    if prop not in self.colnames:
                        c = GeoJSONColumn(name=prop, expr=prop)
                        self.colnames[prop] = c
                        self.addColumn(c)
                yield feature

class GeoJSONMap(InvertedCanvas):
    aspectRatio = 1.0
    filetype = 'geojson'

    @asyncthread
    def reload(self):
        self.reset()

        nplotted = nerrors = 0

        for row in Progress(self.sourceRows):
            k = self.source.rowkey(row)
            colour = self.plotColor(k)

            try:
                bbox = self.parse_geometry(row, colour)
                nplotted += 1
            except Exception as e:
                vd.exceptionCaught(e)
                nerrors += 1
                continue

            x1, y1, x2, y2 = bbox
            textx, texty = (x1+x2)/2, (y1+y2)/2
            disptext = self.textCol.getDisplayValue(row)
            self.label(textx, texty, disptext, colour, row)

        vd.status('loaded %d %s (%d errors)' % (nplotted, self.rowtype, nerrors))
        self.refresh()

    def parse_geometry(self, row, colour, bbox=None):
        if bbox is None: bbox = [180, 90, -180, -90]

        typ = row['geometry']['type']
        if typ == 'GeometryCollection':
            for g in row['geometries']:
                bbox = self.parse_geometry(row, colour, bbox)
            return bbox

        coords = row['geometry']['coordinates']
        if typ in ('Point', 'LineString', 'Polygon'):
            coords = [coords]

        if typ in ('Point', 'MultiPoint'):
            for x, y in coords:
                self.point(x, y, colour, row)
            bbox = reduce_coords(coords, bbox)
        elif typ in ('LineString', 'MultiLineString'):
            for line in coords:
                self.polyline(line, colour, row)
                bbox = reduce_coords(line, bbox)
        elif typ in ('Polygon', 'MultiPolygon'):
            for polygon in coords:
                if not isinstance(polygon[0][0], list):
                    continue
                self.polygon(polygon[0], colour, row)
                bbox = reduce_coords(polygon[0], bbox)
                for hole in polygon[1:]:
                    self.polygon(hole, 0, row)
        else:
            vd.warning('notimpl shapeType %s' % typ)

        return bbox

def reduce_coords(coords, initial):
    return reduce(
        lambda a,n: [min(a[0],n[0]), min(a[1],n[1]), max(a[2],n[0]), max(a[3],n[1])],
        coords, initial)

def _rowdict(cols, row):
    ret = {}
    for col in cols:
        o = wrapply(col.getTypedValue, row)
        if isinstance(o, TypedExceptionWrapper):
            o = col.sheet.options.safe_error or str(o.exception)
        elif isinstance(o, TypedWrapper):
            o = o.val
        elif isinstance(o, date):
            o = col.getDisplayValue(row)
        if o is not None:
            ret[col.name] = o
    return ret

@VisiData.api
def save_geojson(vd, p, vs):
    features = []
    for row in Progress(vs.rows, 'saving'):
        copyrow = deepcopy(row)
        copyrow['properties'] = _rowdict(vs.visibleCols, row)
        features.append(copyrow)

    featcoll = {
        'type': 'FeatureCollection',
        'features': features,
    }

    try:
        indent = int(vs.options.json_indent)
    except Exception:
        indent = vs.options.json_indent

    with p.open_text(mode='w', encoding='utf-8') as fp:
        encoder = json.JSONEncoder(indent=indent, sort_keys=vs.options.json_sort_keys)
        for chunk in encoder.iterencode(featcoll):
            fp.write(chunk)

GeoJSONSheet.addCommand('.', 'plot-row', 'vd.push(GeoJSONMap(name+"_map", sourceRows=[cursorRow], textCol=cursorCol, source=sheet))', 'plot geospatial vector in current row')
GeoJSONSheet.addCommand('g.', 'plot-rows', 'vd.push(GeoJSONMap(name+"_map", sourceRows=rows, textCol=cursorCol, source=sheet))', 'plot all geospatial vectors in current sheet')
GeoJSONMap.addCommand('^S', 'save-sheet', 'vd.saveSheets(inputPath("save to: ", value=getDefaultSaveName(sheet)), sheet, confirm_overwrite=options.confirm_overwrite)', 'save current sheet to filename in format determined by extension (default .geojson)')

vd.addGlobals({
    'GeoJSONMap': GeoJSONMap,
})
