from visidata import *


def open_ttf(p):
    return TTFTablesSheet(p.name, source=p)

open_otf = open_ttf


class TTFTablesSheet(Sheet):
    rowtype = 'font tables'
    columns = [
        ColumnAttr('cmap'),
        ColumnAttr('format', type=int),
        ColumnAttr('language', type=int),
        ColumnAttr('length', type=int),
        ColumnAttr('platEncID', type=int),
        ColumnAttr('platformID', type=int),
        Column('isSymbol', getter=lambda col,row: row.isSymbol()),
        Column('isUnicode', getter=lambda col,row: row.isUnicode()),
    ]

    @asyncthread
    def reload(self):
        import fontTools.ttLib

        self.ttf = fontTools.ttLib.TTFont(self.source.resolve(), 0, allowVID=0, ignoreDecompileErrors=True, fontNumber=-1)
        self.rows = []
        for cmap in self.ttf["cmap"].tables:
            self.addRow(cmap)


class TTFGlyphsSheet(Sheet):
    rowtype = 'glyphs'  # rowdef: (codepoint, glyphid, fontTools.ttLib.ttFont._TTGlyphGlyf)
    columns = [
        ColumnItem('codepoint', 0, type=int, fmtstr='{:0X}'),
        ColumnItem('glyphid', 1),
        SubrowColumn('height', ColumnAttr('height', type=int), 2),
        SubrowColumn('width', ColumnAttr('width', type=int), 2),
        SubrowColumn('lsb', ColumnAttr('lsb'), 2),
        SubrowColumn('tsb', ColumnAttr('tsb'), 2),
    ]

    @asyncthread
    def reload(self):
        self.rows = []
        glyphs = self.ttf.getGlyphSet()
        for cmap in self.sourceRows:
            for codepoint, glyphid in Progress(cmap.cmap.items(), total=len(cmap.cmap)):
                self.addRow((codepoint, glyphid, glyphs[glyphid]))


TTFTablesSheet.addCommand(ENTER, 'dive-row', 'vd.push(TTFGlyphsSheet(name+str(cursorRowIndex), source=sheet, sourceRows=[cursorRow], ttf=ttf))')
TTFGlyphsSheet.addCommand('.', 'plot-row', 'vd.push(makePen(name+"_"+cursorRow[1], source=cursorRow[2], glyphSet=ttf.getGlyphSet()))')


def makePen(*args, **kwargs):
    try:
        from fontTools.pens.basePen import BasePen
    except ImportError as e:
        error('fonttools not installed')

    class GlyphPen(InvertedCanvas, BasePen):
        aspectRatio = 1.0
        def __init__(self, name, **kwargs):
            super().__init__(name, **kwargs)
            self.lastxy = None
            self.attr = self.plotColor(('glyph',))

        def _moveTo(self, xy):
            self.lastxy = xy

        def _lineTo(self, xy):
            x1, y1 = self.lastxy
            x2, y2 = xy
            self.line(x1, y1, x2, y2, self.attr)
            self._moveTo(xy)

        def _curveToOne(self, xy1, xy2, xy3):
            error('NotImplemented')

        def _qCurveToOne(self, xy1, xy2):
            self.qcurve([self.lastxy, xy1, xy2], self.attr)
            self._moveTo(xy2)

        def reload(self):
            self.reset()
            self.source.draw(self)
            self.refresh()

    return GlyphPen(*args, **kwargs)
