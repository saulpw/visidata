from visidata import vd, BaseSheet, ENTER, colors, dispwidth
import curses


def boundingBox(rows):
    'Return (xmin, ymin, xmax, ymax) of rows.'
    xmin, ymin, xmax, ymax = 9999, 9999, 0, 0
    for r in rows:
        if r.x is not None:
            xmin = min(xmin, r.x)
            xmax = max(xmax, r.x + (r.w or dispwidth(r.text or '')))
        if r.y is not None:
            ymin = min(ymin, r.y)
            ymax = max(ymax, r.y + (r.h or 0))
    return xmin, ymin, xmax, ymax


class CharBox:
    def __init__(self, scr=None, x1=0, y1=0, w=None, h=None):
        scrh, scrw = scr.getmaxyx() if scr else (25, 80)
        self.scr = scr
        self.x1 = x1
        self.y1 = y1
        self.w = scrw if w is None else w
        self.h = scrh if h is None else h

        self.normalize()

    def __str__(self):
        return f'({self.x1}+{self.w},{self.y1}+{self.h})'

    def normalize(self):
        'Make sure w and h are non-negative, swapping coordinates as needed.'
        if self.w < 0:
            self.x1 += self.w
            self.w = -self.w

        if self.h < 0:
            self.y1 += self.h
            self.h = -self.h

    @property
    def x2(self):
        return self.x1+self.w+1

    @x2.setter
    def x2(self, v):
        self.w = v-self.x1-1
        self.normalize()

    @property
    def y2(self):
        return self.y1+self.h+1

    @y2.setter
    def y2(self, v):
        self.h = v-self.y1-1
        self.normalize()

    def contains(self, b):
        'Return True if this box contains any part of the given x,y,w,h.'
        xA = max(self.x1, b.x1)  # left
        xB = min(self.x2, b.x2)  # right
        yA = max(self.y1, b.y1)  # top
        yB = min(self.y2, b.y2)  # bottom
        return xA < xB-1 and yA < yB-1   # xA+.5 < xB-.5 and yA+.5 < yB-.5


class TextCanvas(BaseSheet):
    @property
    def rows(self):
        return self.source.rows

    @rows.setter
    def rows(self, v):
        pass

    def reload(self):
        pass

    def draw(self, scr):
        for i in range(self.cursorBox.h):
            for j in range(self.cursorBox.w):
                scr.addstr(self.cursorBox.y1+i, self.cursorBox.x1+j, ' ', colors.color_current_row)

    def commandCursor(self, execstr):
        if 'cursor' in execstr:
            return '%s %s' % (self.cursorBox.x1, self.cursorBox.x2), '%s %s' % (self.cursorBox.y1, self.cursorBox.y2)
        return '', ''

    def checkCursor(self):
        self.cursorBox.x1 = min(self.windowWidth-2, max(0, self.cursorBox.x1))
        self.cursorBox.y1 = min(self.windowHeight-2, max(0, self.cursorBox.y1))

    def iterbox(self, box, n=None):
        'Return *n* top elements from each cell within the given *box*.'
        ret = list()
        for r in self.source.rows:
            if r.pos.x is None or r.pos.y is None: continue
            if box.contains(CharBox(None, r.pos.x, r.pos.y, 1, 1)):
                ret.append(r)

        return ret[:-n] if n else ret

    def itercursor(self, n=None):
        return self.iterbox(self.cursorBox, n=n)

    @property
    def cursorRows(self):
        return list(self.iterbox(self.cursorBox))

    def slide(self, rows, dx, dy):
        maxX, maxY = self.windowWidth, self.windowHeight
        x1, y1, x2, y2 = boundingBox(rows)
        dx = -x1 if x1+dx < 0 else (maxX-x2-1 if x2+dx > maxX-1 else dx)
        dy = -y1 if y1+dy < 0 else (maxY-y2-1 if y2+dy > maxY-1 else dy)
        xcol = self.source.column('x')
        ycol = self.source.column('y')
        for r in rows:
            oldx = xcol.getValue(r)
            oldy = ycol.getValue(r)
            if oldx is not None:
                xcol.setValue(r, oldx+dx)
            if oldy is not None:
                ycol.setValue(r, oldy+dy)


TextCanvas.addCommand('', 'go-down', 'cursorBox.y1 += 1')
TextCanvas.addCommand('', 'go-up', 'cursorBox.y1 -= 1')
TextCanvas.addCommand('', 'go-left', 'cursorBox.x1 -= 1')
TextCanvas.addCommand('', 'go-right', 'cursorBox.x1 += 1')
TextCanvas.addCommand('kRIT5', 'resize-cursor-wider', 'cursorBox.w += 1', 'increase cursor width by one character')
TextCanvas.addCommand('kLFT5', 'resize-cursor-thinner', 'cursorBox.w -= 1', 'decrease cursor width by one character')
TextCanvas.addCommand('kUP5', 'resize-cursor-shorter', 'cursorBox.h -= 1', 'decrease cursor height by one character')
TextCanvas.addCommand('kDN5', 'resize-cursor-taller', 'cursorBox.h += 1', 'increase cursor height by one character')
TextCanvas.addCommand('gzKEY_LEFT', 'resize-cursor-min-width', 'cursorBox.w = 1')
TextCanvas.addCommand('gzKEY_UP', 'resize-cursor-min-height', 'cursorBox.h = 1')
TextCanvas.addCommand('z_', 'resize-cursor-min', 'cursorBox.h = cursorBox.w = 1')
TextCanvas.addCommand('g_', 'resize-cursor-max', 'cursorBox.x1=cursorBox.y1=0; cursorBox.h=maxY+1; cursorBox.w=maxX+1')
TextCanvas.bindkey('zKEY_RIGHT', 'resize-cursor-wider')
TextCanvas.bindkey('zKEY_LEFT', 'resize-cursor-thinner')
TextCanvas.bindkey('zKEY_UP', 'resize-cursor-shorter')
TextCanvas.bindkey('zKEY_DOWN', 'resize-cursor-taller')
TextCanvas.addCommand('BUTTON1_PRESSED', 'move-cursor', 'sheet.cursorBox = CharBox(None, mouseX, mouseY, 1, 1)', 'start cursor box with left mouse button press')
TextCanvas.addCommand('BUTTON1_RELEASED', 'end-cursor', 'cursorBox.x2=mouseX+2; cursorBox.y2=mouseY+2; cursorBox.normalize()', 'end cursor box with left mouse button release')

TextCanvas.addCommand('s', 'select-cursor', 'source.select(cursorRows)')
TextCanvas.addCommand('t', 'toggle-cursor', 'source.toggle(cursorRows)')
TextCanvas.addCommand('u', 'unselect-cursor', 'source.unselect(cursorRows)')
TextCanvas.addCommand('gs', 'select-all', 'source.select(source.rows)')
TextCanvas.addCommand('gt', 'toggle-all', 'source.toggle(source.rows)')
TextCanvas.addCommand('gu', 'unselect-all', 'source.clearSelected()')
TextCanvas.addCommand('zs', 'select-top-cursor', 'source.select(list(itercursor(n=1)))')
TextCanvas.addCommand('zt', 'toggle-top-cursor', 'source.toggle(list(itercursor(n=1)))')
TextCanvas.addCommand('zu', 'unselect-top-cursor', 'source.unselect(list(itercursor(n=1)))')
TextCanvas.addCommand('d', 'delete-cursor', 'source.deleteBy(lambda r,rows=cursorRows: r in rows)', 'delete first item under cursor')
TextCanvas.addCommand('gd', 'delete-selected', 'source.deleteSelected()', 'delete selected rows on source sheet')
TextCanvas.addCommand(ENTER, 'dive-cursor', 'vs=copy(source); vs.rows=cursorRows; vs.source=sheet; vd.push(vs)', 'dive into source rows under cursor')
TextCanvas.addCommand('g'+ENTER, 'dive-selected', 'vd.push(type(source)(source=sheet, rows=source.selectedRows))', 'dive into selected source rows')

TextCanvas.addCommand('H', 'slide-left-obj',       'slide(source.selectedRows, -1, 0)', 'slide selected objects left one character')
TextCanvas.addCommand('J', 'slide-down-obj',       'slide(source.selectedRows, 0, +1)', 'slide selected objects down one character')
TextCanvas.addCommand('K', 'slide-up-obj',         'slide(source.selectedRows, 0, -1)', 'slide selected objects up one character')
TextCanvas.addCommand('L', 'slide-right-obj',      'slide(source.selectedRows, +1, 0)', 'slide selected objects right one character')
TextCanvas.addCommand('gH', 'slide-leftmost-obj',  'slide(source.selectedRows, -maxX, 0)', 'slide selected objects all the way left')
TextCanvas.addCommand('gJ', 'slide-bottom-obj',    'slide(source.selectedRows, 0, +maxY)', 'slide all selected objects all the way bottom')
TextCanvas.addCommand('gK', 'slide-top-obj',       'slide(source.selectedRows, 0, -maxY)', 'slide all selected objects all the way top')
TextCanvas.addCommand('gL', 'slide-rightmost-obj', 'slide(source.selectedRows, +maxX, 0)', 'slide all selected objects all the way right')


TextCanvas.init('cursorBox', lambda: CharBox(None, 0,0,1,1))

vd.addGlobals({
    'CharBox': CharBox,
    'boundingBox': boundingBox,
    'TextCanvas': TextCanvas,
    })
