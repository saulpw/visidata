from unittest import mock
import random
import time
import unicodedata
from visidata import *
from .box import CharBox


vd.allPrefixes += list('01')
vd.option('pen_down', False, 'is pen down')

vd.charPalWidth = charPalWidth = 16
vd.charPalHeight = charPalHeight = 16

@VisiData.api
def open_ddw(vd, p):
    vd.timeouts_before_idle = 60
    return DrawingSheet(p.name, 'table', source=p).drawing

vd.save_ddw = vd.save_jsonl

@VisiData.lazy_property
def words(vd):
    return [x.strip() for x in open('/usr/share/dict/words').readlines() if 3 <= len(x) < 8 and x.islower() and x.strip().isalpha()]

@VisiData.api
def random_word(vd):
    return random.choice(vd.words)

def bounding_box(rows):
    'Return (xmin, ymin, xmax, ymax) of rows.'
    xmin, ymin, xmax, ymax = 9999, 9999, 0, 0
    for r in rows:
        if r.x is not None:
            xmin = min(xmin, r.x)
            xmax = max(xmax, r.x + (r.w or 0))
        if r.y is not None:
            ymin = min(ymin, r.y)
            ymax = max(ymax, r.y + (r.h or 0))
    return xmin, ymin, xmax, ymax

def any_match(G1, G2):
    if G1 and G2:
        for g in G1:
            if g in G2: return True

class FramesSheet(Sheet):
    rowtype='frames'  # rowdef: { .type, .id, .duration_ms, .x, .y }
    columns = [
        ItemColumn('type', width=0),
        ItemColumn('id'),
        ItemColumn('duration_ms', type=int),
        ItemColumn('x', type=int),
        ItemColumn('y', type=int),
    ]

class DrawingSheet(JsonSheet):
    rowtype='elements'  # rowdef: { .type, .x, .y, .text, .color, .group, .tags=[], .frame, .id, .rows=[] }
    columns=[
        ItemColumn('id'),
        ItemColumn('type'),
        ItemColumn('x', type=int),
        ItemColumn('y', type=int),

        ItemColumn('text'),  # for text objects (type == '')
        ItemColumn('color'), # for text

        # for all objects
        ItemColumn('tags'),  # for all objs
        ItemColumn('group'), # "
        ItemColumn('frame'), # "

        ItemColumn('rows'), # for groups
        ItemColumn('duration_ms', type=int), # for frames

        ItemColumn('ref'),
    ]
    colorizers = [
        CellColorizer(3, None, lambda s,c,r,v: r and c and c.name == 'text' and r.color)
    ]
    def newRow(self):
        return AttrDict(x=None, y=None, text='', color='', tags=[], group='')

    @functools.cached_property
    def drawing(self):
        return Drawing(self.name, source=self)

    def addRow(self, row, **kwargs):
        row = super().addRow(row, **kwargs)
        vd.addUndo(self.rows.remove, row)
        return row

    def iterdeep(self, rows, x=0, y=0, parents=None):
        for r in rows:
            newparents = (parents or []) + [r]
            if r.type == 'frame': continue
            if r.ref:
                assert r.type == 'ref'
                g = self.groups[r.ref]
                yield from self.iterdeep(g.rows, x+r.x, y+r.y, newparents)
            else:
                yield r, x+r.x, y+r.y, newparents
                yield from self.iterdeep(r.rows or [], x+r.x, x+r.y, newparents)

    def tag_rows(self, rows, tagstr):
        tags = tagstr.split()
        for r in rows:
            if not r.tags: r.tags = []
            for tag in tags:
                if tag not in r.tags:
                    r.tags.append(tag)

    @property
    def groups(self):
        return {r.id:r for r in self.rows if r.type == 'group'}

    def create_group(self, gname):
        nr = self.newRow()
        nr.id = gname
        nr.type = 'group'
        vd.status('created group "%s"' % gname)
        return self.addRow(nr)

    @drawcache_property
    def frames(self):
        return [r for r in self.rows if r.type == 'frame']

    @property
    def nFrames(self):
        return len(self.frames)

    def new_between_frame(self, fidx1, fidx2):
        f1 = f2 = None
        if not self.frames:
            name = '0'
        else:
            if 0 <= fidx1 < len(self.frames):
                f1 = self.frames[fidx1]
            if 0 <= fidx2 < len(self.frames):
                f2 = self.frames[fidx2]
            if f1 and f2:
                name = str(f1.id)+'-'+str(f2.id)
            elif f1:
                name = str(int(f1.id)+1)
            elif f2:
                name = str(int(f1.id)-1)

        newf = self.newRow()
        newf.type = 'frame'
        newf.id = name
        newf.duration_ms = 100
        if f1:
            for i, r in enumerate(self.rows):
                if r is f1:
                    return self.addRow(newf, index=i+1)
        else:
            return self.addRow(newf, index=0)
        vd.error('no existing frame ' + str(f1))

    def group_selected(self, gname):
        nr = self.create_group(gname)

        rows = self.selectedRows
        nr.rows = rows
        x1, y1, x2, y2 = bounding_box(nr.rows)
        nr.x, nr.y, nr.w, nr.h = x1, y1, x2-x1, y2-y1
        for r in nr.rows:
            r.x = (r.x or 0) - x1
            r.y = (r.y or 0) - y1

        self.deleteSelected()
        self.select([nr])
        vd.status('group "%s" (%d objects)' % (gname, self.nSelectedRows))

    def regroup_selected(self):
        regrouped = []
        groups = set()  # that items were grouped into
        for r in self.someSelectedRows:
            if r.group:
                regrouped.append(r)
                if r.group not in self.groups:
                    g = self.create_group(r.group)
                    g.x = r.x
                    g.y = r.y
                    self.addRow(g)
                else:
                    g = self.groups[r.group]

                r.x -= g.x
                r.y -= g.y
                g.rows.append(r)
                groups.add(r.group)

        self.deleteBy(lambda r,rows=regrouped: r in rows)
        self.select(list(g for name, g in self.groups.items() if name in groups))

        vd.status('regrouped %d %s' % (len(regrouped), self.rowtype))

    def degroup_selected(self):
        degrouped = []
        groups = set()
        for r, x, y, parents in self.iterdeep(self.someSelectedRows):
            r.x = x
            r.y = y
            r.group = '.'.join((p.id or '') for p in parents[:-1])

            if r.type == 'group':
                groups.add(r.id)

            if r is not parents[0]:
                self.addRow(r)
                degrouped.append(r)

        for g in groups:
            oldrows = copy(self.groups[g].rows)
            self.groups[g].rows.clear()
            vd.addUndo(setattr, self.groups[g], 'rows', oldrows)

        self.clearSelected()
        self.select(degrouped)
        vd.status('ungrouped %d %s' % (len(degrouped), self.rowtype))

    def gatherTag(self, gname):
        return list(r for r in self.rows if gname in r.get('group', ''))

    def slide_top(self, rows, index=0):
        'Move selected rows to top of sheet (bottom of drawing)'
        for r in rows:
            self.rows.pop(self.rows.index(r))
            self.rows.insert(index, r)


class Drawing(BaseSheet):
    def iterbox(self, box):
        'Yield rows within the given box.'
        for nx in range(box.x1, box.x2-1):
            for ny in range(box.y1, box.y2-1):
                yield from self._displayedRows[(nx,ny)]

    @property
    def rows(self):
        return self.source.rows

    @rows.setter
    def rows(self, v):
        pass

    def __getattr__(self, k):
        return getattr(self.source, k)

    @property
    def currentFrame(self):
        if self.frames and 0 <= self.cursorFrameIndex < self.nFrames:
            return self.frames[self.cursorFrameIndex]
        return AttrDict()

    def commandCursor(self, execstr):
        if 'cursor' in execstr:
            return '%s %s' % (self.cursorBox.x1, self.cursorBox.x2), '%s %s' % (self.cursorBox.y1, self.cursorBox.y2)
        return '', ''

    def moveToRow(self, rowstr):
        self.refresh()
        a, b = map(int, rowstr.split())
        self.cursorBox.y1, self.cursorBox.y2 = a, b
        return True

    def moveToCol(self, colstr):
        self.refresh()
        a, b = map(int, colstr.split())
        self.cursorBox.x1, self.cursorBox.x2 = a, b
        return True

    def itercursor(self):
        return self.iterbox(self.cursorBox)

    def refresh(self):
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))
        self.draw(self._scr)

    def draw(self, scr):
        vd.getHelpPane('darkdraw').draw(scr, y=-1, x=-1)

        thisframe = self.currentFrame
        if self.autoplay_frames:
            vd.timeouts_before_idle = -1
            t = time.time()
            ft, f = self.autoplay_frames[0]
            thisframe = f
            if not ft:
                self.autoplay_frames[0][0] = t
            elif t-ft > f.duration_ms/1000:  # frame expired
#                vd.status('next frame after %0.3fs' % (t-ft))
                self.autoplay_frames.pop(0)
                if self.autoplay_frames:
                    self.autoplay_frames[0][0] = t
                    thisframe = self.autoplay_frames[0][1]
                    vd.curses_timeout = thisframe.duration_ms
                else:
                    vd.status('ending autoplay')
                    vd.timeouts_before_idle = 10
                    vd.curses_timeout = 100

        self._displayedRows = defaultdict(list)  # (x, y) -> list of rows; actual screen layout (topmost last in list)
        self._tags = defaultdict(list)  # "tag" -> list of rows with that tag

        selectedGroups = set()  # any group with a selected element

        # draw blank cursor as backdrop
        for i in range(self.cursorBox.h):
            for j in range(self.cursorBox.w):
                clipdraw(scr, self.cursorBox.y1+i, self.cursorBox.x1+j, ' ', colors.color_current_row)

        self.minX, self.minY, self.maxX, self.maxY = bounding_box(self.source.rows)

        for r, x, y, parents in self.iterdeep(self.source.rows):
            toprow = parents[0]
            for g in (r.tags or []):
                self._tags[g].append(r)

            if not r.text: continue
            if any_match(r.tags, self.disabled_tags): continue
            if toprow.frame or r.frame:
                if not self.frames: continue
                if thisframe.id not in [toprow.frame, r.frame]: continue

            if not (0 <= y < self.windowHeight-1 and 0 <= x < self.windowWidth):  # inside screen
                continue

            c = r.color or ''
            if self.cursorBox.contains(CharBox(scr, x, y, r.w or dispwidth(r.text), r.h or 1)):
                c = self.options.color_current_row + ' ' + str(c)
            if self.source.isSelected(toprow):
                c = self.options.color_selected_row + ' ' + str(c)
                if r.tags: selectedGroups |= set(r.tags)
            a = colors[c]
            w = clipdraw(scr, y, x, r.text, a)
            for i in range(0, w):
                cellrows = self._displayedRows[(x+i, y)]
                if toprow not in cellrows:
                    cellrows.append(toprow)

        defcolor = self.options.color_default
        defattr = colors[defcolor]
        if self.options.visibility == 1: # draw tags
            clipdraw(scr, 0, self.windowWidth-20, '00: (reset)', defattr)
            for i, tag in enumerate(self._tags.keys()):
                c = defcolor
                if tag in self.disabled_tags:
                    c = self.options.color_graph_hidden
                if self.cursorRow and tag in self.cursorRow.get('group', ''):
                    c = self.options.color_current_row + ' ' + c
                if tag in selectedGroups:
                    c = self.options.color_selected_row + ' ' + c
                clipdraw(scr, i+1, self.windowWidth-20, 'z%02d: %s' % (i+1, tag), colors[c])

        elif self.options.visibility == 2: # draw clipboard item shortcuts
            if not vd.memory.cliprows:
                return
            for i, r in enumerate(vd.memory.cliprows[:10]):
                x = self.windowWidth-20
                x += clipdraw(scr, i+1, x, '%d: ' % (i+1), defattr)
                x += clipdraw(scr, i+1, x, r.text, colors[r.color])


        x = 3
        y = self.windowHeight-2
        x += clipdraw(scr, y, x, 'paste ' + self.paste_mode + ' ', defattr)

        x += clipdraw(scr, y, x, ' %s %s ' % (len(vd.memory.cliprows or []), self.rowtype), defattr)

        x += clipdraw(scr, y, x, '  default color: ', defattr)
        x += clipdraw(scr, y, x, '##', colors[vd.default_color])
        x += clipdraw(scr, y, x, ' %s' % vd.default_color, defattr)

    def reload(self):
        self.source.ensureLoaded()
        vd.sync()
        self.draw(self._scr)

    def place_text(self, text, x=None, y=None, dx=0, dy=0):
        'Return (width, height) of drawn text.'
        if x is None: x = self.cursorBox.x1
        if y is None: y = self.cursorBox.y1
        r = self.newRow()
        r.x, r.y, r.text = x, y, text
        self.source.addRow(r)
        self.modified = True
        self.go_forward(dispwidth(text)+dx, 1+dy)
        if self.cursorBox.x1 > self.windowWidth:
            self.cursorBox.x1 = 1
            self.cursorBox.y1 += 1
        if self.cursorBox.y1 > self.windowHeight-1:
            self.cursorBox.x1 += 1
            self.cursorBox.y1 = 1

    def edit_text(self, text, row):
        if row is None:
            self.place_text(text, dx=1)
            return
        oldtext = row.text
        row.text = text
        vd.addUndo(setattr, row, 'text', oldtext)


    def get_text(self, x=None, y=None):
        'Return text of topmost visible element at (x,y) (or cursor if not given).'
        if x is None: x = self.cursorBox.x1
        if y is None: y = self.cursorBox.y1
        r = self._displayedRows.get((x,y), None)
        if not r: return ''
        return r[-1]['text']

    def remove_at(self, box):
        rows = list(self.iterbox(box))
        self.source.deleteBy(lambda r,rows=rows: r in rows)
        return rows

    @property
    def cursorRows(self):
        return list(self.iterbox(self.cursorBox))

    @property
    def cursorRow(self):
        cr = self.cursorRows
        if cr: return cr[-1]

    @property
    def cursorChar(self):
        cr = self.cursorRow
        if cr: return cr.get('text', '')
        return ''

    @property
    def cursorDesc(self):
        cr = self.cursorRow
        if cr and cr.text:
            return 'U+%04X' % ord(cr.text[0])
        if cr and cr.type == 'group':
            n = len(list(self.iterdeep(cr.rows)))
            return '%s (%s objects)' % (cr.id, n)
        return '???'

    @property
    def frameDesc(sheet):
        return f'Frame {sheet.currentFrame.id} {sheet.cursorFrameIndex}/{sheet.nFrames-1}'

    @property
    def cursorCharName(self):
        ch = self.cursorChar
        if not ch: return ''
        return unicodedata.name(ch[0])

    def go_left(self):
        if self.options.pen_down:
            self.pendir = 'l'
            self.place_text(ch, self.cursorBox.x1, self.cursorBox.y1, **vd.memory.cliprows[0])
        else:
            self.cursorBox.x1 -= 1

    def go_right(self):
        if self.options.pen_down:
            self.pendir = 'r'
            self.place_text(ch, self.cursorBox.x1, self.cursorBox.y1, **vd.memory.cliprows[0])
        else:
            self.cursorBox.x1 += 1

    def go_down(self):
        if self.options.pen_down:
            self.pendir = 'd'
            self.place_text(ch, self.cursorBox.x1, self.cursorBox.y1, **vd.memory.cliprows[0])
        else:
            self.cursorBox.y1 += 1

    def go_up(self):
        if self.options.pen_down:
            self.pendir = 'u'
            self.place_text(ch, self.cursorBox.x1, self.cursorBox.y1, **vd.memory.cliprows[0])
        else:
            self.cursorBox.y1 -= 1

    def go_pagedown(self, n):
        self.cursorBox.y1 = self.windowHeight-2

    def go_leftmost(self):
        self.cursorBox.x1 = 0

    def go_rightmost(self):
        self.cursorBox.x1 = self.maxX

    def go_top(self):
        self.cursorBox.y1 = 0

    def go_bottom(self):
        self.cursorBox.y1 = self.maxY

    def go_forward(self, x, y):
        if self.pendir == 'd': self.cursorBox.y1 += y
        elif self.pendir == 'u': self.cursorBox.y1 -= y
        elif self.pendir == 'r': self.cursorBox.x1 += x
        elif self.pendir == 'l': self.cursorBox.x1 -= x

    def slide_selected(self, dx, dy):
        for r in self.source.someSelectedRows:
            if 'x' in r: r['x'] += dx
            if 'y' in r: r['y'] += dy

    def go_obj(self, xdir=0, ydir=0):
        x=self.cursorBox.x1
        y=self.cursorBox.y1
        currows = self._displayedRows.get((x, y), [])
        xmin = min(x for x, y in self._displayedRows.keys())
        ymin = min(y for x, y in self._displayedRows.keys())
        xmax = max(x for x, y in self._displayedRows.keys())
        ymax = max(y for x, y in self._displayedRows.keys())

        while xmin <= x <= xmax and ymin <= y <= ymax:
            for r in self._displayedRows.get((x, y), [])[::-1]:
                if r and r not in currows:
                    self.cursorBox.x1 = x
                    self.cursorBox.y1 = y
                    return
            x += xdir
            y += ydir

    def checkCursor(self):
        self.cursorBox.x1 = min(self.windowWidth-2, max(0, self.cursorBox.x1))
        self.cursorBox.y1 = min(self.windowHeight-2, max(0, self.cursorBox.y1))
        self.cursorFrameIndex = min(max(self.cursorFrameIndex, 0), len(self.frames)-1)

    def end_cursor(self, x, y):
        self.cursorBox.x2 = x+2
        self.cursorBox.y2 = y+2
        self.cursorBox.normalize()

    def join_rows(dwg, rows):
        vd.addUndo(setattr, rows[0], 'text', rows[0].text)
        rows[0].text = ''.join(r.text for r in rows)
        dwg.source.deleteBy(lambda r,rows=rows[1:]: r in rows)

    def cycle_paste_mode(self):
        modes = ['all', 'char', 'color']
        self.paste_mode = modes[(modes.index(self.paste_mode)+1)%len(modes)]

    def paste_chars(self, srcrows):
        srcrows or vd.fail('no rows to paste')

        newrows = []

        x1, y1, x2, y2 = bounding_box(srcrows)
        for oldr in srcrows:
            if oldr.x is None:
                newx = self.cursorBox.x1
                newy = self.cursorBox.y1
                if len(srcrows) > 1:
                    self.go_forward(dispwidth(r.text)+1, 1)
            else:
                newx = (oldr.x or 0)+self.cursorBox.x1-x1
                newy = (oldr.y or 0)+self.cursorBox.y1-y1

            if self.paste_mode in 'all char':
                r = self.newRow()
                r.update(deepcopy(oldr))
                r.frame = self.currentFrame.id
                r.text = oldr.text
                r.x, r.y = newx, newy
                if self.paste_mode == 'char':
                    r.color = vd.default_color
                newrows.append(r)
                self.source.addRow(r)
            elif self.paste_mode == 'color':
                if oldr.color:
                    for existing in self._displayedRows[(newx, newy)]:
                        existing.color = oldr.color

    def paste_groupref(self, rows):
        for r in rows:
            if r.type == 'group':
                newr = self.newRow()
                newr.type = 'ref'
                newr.x, newr.y = self.cursorBox.x1, self.cursorBox.y1
                newr.ref = r.id
                self.addRow(newr)
            else:
                vd.warning('not a group')

    def select_tag(self, tag):
        self.select(list(r for r in self.source.rows if tag in (r.tags or '')))

    def unselect_tag(self, tag):
        self.unselect(list(r for r in self.rows if tag in (r.tags or '')))

    def align_selected(self, attrname):
        rows = self.someSelectedRows
        for r in rows:
            r.x = rows[0].x


Drawing.init('cursorBox', lambda: CharBox(None, 0,0,1,1))
Drawing.init('_displayedRows', dict)  # (x,y) -> list of rows
Drawing.init('pendir', lambda: 'r')
Drawing.init('disabled_tags', set)  # set of groupnames which should not be drawn or interacted with

Drawing.addCommand(None, 'go-left',  'go_left()', 'go left one char')
Drawing.addCommand(None, 'go-down',  'go_down()', 'go down one char')
Drawing.addCommand(None, 'go-up',    'go_up()', 'go up one char')
Drawing.addCommand(None, 'go-right', 'go_right()', 'go right one char in the palette')
Drawing.addCommand(None, 'go-pagedown', 'go_pagedown(+1);', 'scroll one page forward in the palette')
Drawing.addCommand(None, 'go-pageup', 'go_pagedown(-1)', 'scroll one page backward in the palette')

Drawing.addCommand(None, 'go-leftmost', 'go_leftmost()', 'go all the way to the left of the palette')
Drawing.addCommand(None, 'go-top', 'go_top()', 'go all the way to the top of the palette')
Drawing.addCommand(None, 'go-bottom', 'go_bottom()', 'go all the way to the bottom ')
Drawing.addCommand(None, 'go-rightmost', 'go_rightmost()', 'go all the way to the right')

Drawing.addCommand('', 'pen-left', 'sheet.pendir="l"', '')
Drawing.addCommand('', 'pen-down', 'sheet.pendir="d"', '')
Drawing.addCommand('', 'pen-up', 'sheet.pendir="u"', '')
Drawing.addCommand('', 'pen-right', 'sheet.pendir="r"', '')

Drawing.addCommand('BUTTON1_PRESSED', 'move-cursor', 'sheet.cursorBox = CharBox(None, mouseX, mouseY, 1, 1)', 'start cursor box with left mouse button press')
Drawing.addCommand('BUTTON1_RELEASED', 'end-cursor', 'end_cursor(mouseX, mouseY)', 'end cursor box with left mouse button release')

Drawing.addCommand('', 'align-x-selected', 'align_selected("x")')

Drawing.addCommand('F', 'open-frames', 'vd.push(FramesSheet(sheet, "frames", source=sheet, rows=sheet.frames, cursorRowIndex=sheet.cursorFrameIndex))')
Drawing.addCommand('[', 'prev-frame', 'sheet.cursorFrameIndex -= 1 if sheet.cursorFrameIndex > 0 else fail("first frame")')
Drawing.addCommand(']', 'next-frame', 'sheet.cursorFrameIndex += 1 if sheet.cursorFrameIndex < sheet.nFrames-1 else fail("last frame")')
Drawing.addCommand('g[', 'first-frame', 'sheet.cursorFrameIndex = 0')
Drawing.addCommand('g]', 'last-frame', 'sheet.cursorFrameIndex = sheet.nFrames-1')
Drawing.addCommand('z[', 'new-frame-before', 'sheet.new_between_frame(sheet.cursorFrameIndex-1, sheet.cursorFrameIndex)')
Drawing.addCommand('z]', 'new-frame-after', 'sheet.new_between_frame(sheet.cursorFrameIndex, sheet.cursorFrameIndex+1); sheet.cursorFrameIndex += 1')

DrawingSheet.unbindkey('[')  # dangerous
DrawingSheet.unbindkey(']')

Drawing.addCommand('g^^', 'jump-first', 'vd.activeStack.append(vd.activeStack.pop(0))', 'jump to first sheet')
Drawing.addCommand('gKEY_HOME', 'slide-top-selected', 'source.slide_top(source.someSelectedRows, -1)', 'move selected items to top layer of drawing')
Drawing.addCommand('gKEY_END', 'slide-bottom-selected', 'source.slide_top(source.someSelectedRows, 0)', 'move selected items to bottom layer of drawing')
Drawing.addCommand('d', 'delete-cursor', 'remove_at(cursorBox)', 'delete first item under cursor')
Drawing.addCommand('gd', 'delete-selected', 'source.deleteSelected()')
Drawing.addCommand('a', 'add-input', 'place_text(input("text: ", value=get_text()), dx=1)')
Drawing.addCommand('e', 'edit-char', 'edit_text(input("text: ", value=get_text()), cursorRow)')
Drawing.addCommand('ge', 'edit-selected', 'v=input("text: ", value=get_text())\nfor r in source.selectedRows: r.text=v')
Drawing.addCommand('y', 'yank-char', 'sheet.copyRows([cursorRow])')
Drawing.addCommand('gy', 'yank-selected', 'sheet.copyRows(sheet.selectedRows)')
Drawing.addCommand('x', 'cut-char', 'sheet.copyRows(remove_at(cursorBox))')
Drawing.addCommand('zx', 'cut-char-top', 'r=list(itercursor())[-1]; sheet.copyRows([r]); source.deleteBy(lambda r,row=r: r is row)')
Drawing.addCommand('p', 'paste-chars', 'sheet.paste_chars(vd.memory.cliprows)')
Drawing.addCommand('zp', 'paste-group', 'sheet.paste_groupref(vd.memory.cliprows)')

Drawing.addCommand('zh', 'go-left-obj', 'go_obj(-1, 0)')
Drawing.addCommand('zj', 'go-down-obj', 'go_obj(0, +1)')
Drawing.addCommand('zk', 'go-up-obj', 'go_obj(0, -1)')
Drawing.addCommand('zl', 'go-right-obj', 'go_obj(+1, 0)')

Drawing.addCommand('H', 'slide-left-obj', 'slide_selected(-1, 0)')
Drawing.addCommand('J', 'slide-down-obj', 'slide_selected(0, +1)')
Drawing.addCommand('K', 'slide-up-obj', 'slide_selected(0, -1)')
Drawing.addCommand('L', 'slide-right-obj', 'slide_selected(+1, 0)')

Drawing.addCommand('G', 'group-selected', 'sheet.group_selected(input("group name: ", value=random_word()))')
Drawing.addCommand('gG', 'regroup-selected', 'sheet.regroup_selected()')
Drawing.addCommand('zG', 'degroup-selected-temp', 'sheet.degroup_selected()')
Drawing.addCommand('gzG', 'degroup-selected-perm', 'sheet.degroup_all()')
DrawingSheet.addCommand('G', 'group-selected', 'sheet.group_selected(input("group name: ", value=random_word()))')
DrawingSheet.addCommand('zG', 'degroup-selected', 'sheet.degroup_selected()')
DrawingSheet.addCommand('gG', 'regroup-selected', 'sheet.regroup_selected()')
Drawing.addCommand(',', 'select-equal-char', 'sheet.select(list(source.gatherBy(lambda r,ch=cursorChar: r.text==ch)))')
Drawing.addCommand('|', 'select-tag', 'sheet.select_tag(input("select tag: ", type="group"))')
Drawing.addCommand('\\', 'unselect-tag', 'sheet.unselect_tag(input("unselect tag: ", type="group"))')

Drawing.addCommand('gs', 'select-all', 'source.select(source.rows)')
Drawing.addCommand('gt', 'toggle-all', 'source.toggle(source.rows)')
Drawing.addCommand('s', 'select-cursor', 'source.select(list(itercursor()))')
Drawing.addCommand('t', 'toggle-cursor', 'source.toggle(list(itercursor()))')
Drawing.addCommand('u', 'unselect-cursor', 'source.unselect(list(itercursor()))')
Drawing.addCommand('zs', 'select-top-cursor', 'source.selectRow(list(itercursor())[-1])')
Drawing.addCommand('gu', 'unselect-all', 'source.clearSelected()')

Drawing.addCommand('z00', 'enable-all-groups', 'disabled_tags.clear()')
for i in range(1, 99):
    Drawing.addCommand('z%02d'%i, 'toggle-enabled-group-%s'%i, 'g=list(_tags.keys())[%s]; disabled_tags.remove(g) if g in disabled_tags else disabled_tags.add(g)' %(i-1))
    Drawing.addCommand('g%02d'%i, 'select-group-%s'%i, 'g=list(_tags.keys())[%s]; source.select(source.gatherTag(g))' %(i-1))
    Drawing.addCommand('gz%02d'%i, 'unselect-group-%s'%i, 'g=list(_tags.keys())[%s]; source.unselect(source.gatherTag(g))' %(i-1))


Drawing.addCommand('A', 'new-drawing', 'vd.push(Drawing("untitled", source=DrawingSheet("", source=Path("untitled.ddw"))))')
Drawing.addCommand('M', 'open-unicode', 'vd.push(vd.unibrowser)')
Drawing.addCommand('`', 'push-source', 'vd.push(sheet.source)')
DrawingSheet.addCommand('`', 'open-drawing', 'vd.push(sheet.drawing)')

Drawing.addCommand('^G', 'show-char', 'status(f"{sheet.cursorBox} <{cursorDesc}> {sheet.cursorCharName}")')
DrawingSheet.addCommand(ENTER, 'dive-group', 'cursorRow.rows or fail("no elements in group"); vd.push(DrawingSheet(source=sheet, rows=cursorRow.rows))')
DrawingSheet.addCommand('g'+ENTER, 'dive-selected', 'ret=sum(((r.rows or []) for r in selectedRows), []) or fail("no groups"); vd.push(DrawingSheet(source=sheet, rows=ret))')
Drawing.addCommand('&', 'join-selected', 'join_rows(source.selectedRows)')

@VisiData.api
def cycleColor(vd, c, n=1):
    return ''.join(str(int(x)+n) if x.isdigit() else x for x in c.split())

Drawing.addCommand('gc', 'set-color-input', 'x=input("color: ", value=sheet.cursorRows[0].color)\nfor r in sheet.cursorRows: r.color=x')
Drawing.addCommand('zc', 'cycle-color', 'for r in sheet.cursorRows: r.color = cycleColor(r.color)')

Drawing.addCommand('gm', 'tag-selected', 'sheet.tag_rows(sheet.someSelectedRows, vd.input("tag selected as: ", type="tag"))')

Drawing.addCommand(ENTER, 'dive-cursor', 'vd.push(DrawingSheet(source=sheet, rows=cursorRows))')
Drawing.addCommand('g'+ENTER, 'dive-selected', 'vd.push(DrawingSheet(source=sheet, rows=source.selectedRows))')
Drawing.addCommand('{', 'go-prev-selected', 'source.moveToNextRow(lambda row,source=source: source.isSelected(row), reverse=True) or fail("no previous selected row"); sheet.cursorBox.x1=source.cursorRow.x; sheet.cursorBox.y1=source.cursorRow.y', 'go to previous selected row'),
Drawing.addCommand('}', 'go-next-selected', 'source.moveToNextRow(lambda row,source=source: source.isSelected(row)) or fail("no next selected row"); sheet.cursorBox.x1=source.cursorRow.x; sheet.cursorBox.y1=source.cursorRow.y', 'go to next selected row'),
Drawing.addCommand('z'+ENTER, 'dive-cursor-group', 'vd.push(DrawingSheet(source=sheet, rows=rows_by_group(cursorRow["group"])))')
Drawing.addCommand('z^Y', 'pyobj-cursor', 'vd.push(PyobjSheet("cursor_top", source=cursorRow))')
Drawing.addCommand('^Y', 'pyobj-cursor', 'vd.push(PyobjSheet("cursor", source=cursorRows))')

Drawing.addCommand('^S', 'save-sheet', 'vd.saveSheets(inputPath("save to: ", value=source.getDefaultSaveName()), sheet.source, confirm_overwrite=options.confirm_overwrite)', 'save current drawing')
Drawing.addCommand('i', 'insert-row', 'for r in source.someSelectedRows: r.y += (r.y >= cursorBox.y1)', '')
Drawing.addCommand('zi', 'insert-col', 'for r in source.someSelectedRows: r.x += (r.x >= cursorBox.x1)', '')

Drawing.addCommand('zm', 'place-mark', 'sheet.mark=(cursorBox.x1, cursorBox.y1)')
Drawing.addCommand('m', 'swap-mark', '(cursorBox.x1, cursorBox.y1), sheet.mark=sheet.mark, (cursorBox.x1, cursorBox.y1)')
Drawing.addCommand('v', 'visibility', 'options.visibility = (options.visibility+1)%3')
Drawing.addCommand('r', 'reset-time', 'sheet.autoplay_frames = [[0, f] for f in sheet.frames]')
Drawing.addCommand('c', 'set-default-color', 'vd.default_color=list(itercursor())[-1].color')

Drawing.addCommand('kRIT5', 'resize-cursor-wider', 'sheet.cursorBox.w += 1')
Drawing.addCommand('kLFT5', 'resize-cursor-thinner', 'sheet.cursorBox.w -= 1')
Drawing.addCommand('kUP5', 'resize-cursor-shorter', 'sheet.cursorBox.h -= 1')
Drawing.addCommand('kDN5', 'resize-cursor-taller', 'sheet.cursorBox.h += 1')

Drawing.addCommand('gzKEY_LEFT', 'resize-cursor-min-width', 'sheet.cursorBox.w = 1')
Drawing.addCommand('gzKEY_UP', 'resize-cursor-min-height', 'sheet.cursorBox.h = 1')

Drawing.addCommand(';', 'cycle-paste-mode', 'sheet.cycle_paste_mode()')
Drawing.addCommand('^G', 'toggle-help', 'vd.show_help = not vd.show_help')

for i in range(1,10):
    Drawing.addCommand('%s'%str(i)[-1], 'paste-char-%d'%i, 'sheet.paste_chars([vd.memory.cliprows[%d]])'%(i-1))

Drawing.bindkey('zKEY_RIGHT', 'resize-cursor-wider')
Drawing.bindkey('zKEY_LEFT', 'resize-cursor-thinner')
Drawing.bindkey('zKEY_UP', 'resize-cursor-shorter')
Drawing.bindkey('zKEY_DOWN', 'resize-cursor-taller')

Drawing.bindkey('C', 'open-colors')
Drawing.unbindkey('^R')

Drawing.init('mark', lambda: (0,0))
Drawing.init('paste_mode', lambda: 'all')
Drawing.init('cursorFrameIndex', lambda: 0)
Drawing.init('autoplay_frames', list)
vd.default_color = ''
Drawing.class_options.disp_rstatus_fmt='{sheet.cursorBox} | {sheet.frameDesc} | {sheet.source.nRows} {sheet.rowtype}  {sheet.options.disp_selected_note}{sheet.source.nSelectedRows}'
Drawing.class_options.quitguard='modified'
Drawing.class_options.null_value=''
DrawingSheet.class_options.null_value=''
