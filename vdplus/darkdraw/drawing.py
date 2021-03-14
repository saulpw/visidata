from unittest import mock
import random
import time
import unicodedata
from visidata import *


vd.allPrefixes += list('01')
vd.option('pen_down', False, 'is pen down')

vd.charPalWidth = charPalWidth = 16
vd.charPalHeight = charPalHeight = 16
vd.first_t = 0
vd.last_t = 0
vd.fixed_t = None

@VisiData.api
def open_ddw(vd, p):
    return Drawing(p.name, source=DrawingSheet(p.name, 'table', source=p))

vd.save_ddw = vd.save_jsonl

@VisiData.lazy_property
def words(vd):
    return [x.strip() for x in open('/usr/share/dict/words').readlines() if 3 <= len(x) < 8 and x.islower()]

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

def iterdeep(rows, x=0, y=0, toprow=None):
    for r in rows:
        yield r, x+r.x, y+r.y, toprow or r
        yield from iterdeep(r.rows or [], x+r.x, x+r.y, toprow or r)

def adj_xy(dx, dy, L):
    for r in L:
        r["x"] += dx
        r["y"] += dy
    return L

def any_match(G1, G2):
    for g in G1:
        if g in G2: return True

def termcolor_to_css_color(n):
    if not n.isdigit():
        return n
    n = int(n)
    if 0 <= n < 16:
        raise
    if 16 <= n < 232:
        n -= 16
        r,g,b = n//36,(n%36)//6,n%6
        ints = [0x00, 0x66, 0x88,0xbb,0xdd,0xff]
        r,g,b=ints[r],ints[g],ints[b]
    else:
        n=list(range(8,255,10))[n-232]
        r,g,b=n,n,n
    return '#%02x%02x%02x' % (r,g,b)


@VisiData.api
def save_ansihtml(vd, p, *sheets):
    for vs in sheets:
        if isinstance(vs, DrawingSheet):
            dwg = Drawing('', source=vs)
        elif isinstance(vs, Drawing):
            dwg = vs
        else:
            vd.fail(f'{vs.name} not a drawing')
        dwg._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))
        dwg.draw(dwg._scr)
        body = '''<pre>'''
        for y in range(dwg.minY, dwg.maxY+1):
            for x in range(dwg.minX, dwg.maxX+1):
                r = dwg.drawing.get((x,y), None)
                if not r:
                    body += ' '
                else:
                    ch = r[-1].text[x-r[-1].x]
                    fg, bg, attrs = colors.split_colorstr(r[-1].color)

                    style = ''
                    if 'underline' in attrs:
                        style += f'text-decoration: underline; '
                    if 'bold' in attrs:
                        style += f'font-weight: bold; '
                    if 'reverse' in attrs:
                        bg, fg = fg, bg
                    if bg:
                        bg = termcolor_to_css_color(bg)
                        style += f'background-color: {bg}; '
                    if fg:
                        fg = termcolor_to_css_color(fg)
                        style += f'color: {fg}; '

                    body += f'<span style="{style}">{ch}</span>'
            body += '\n'
        body += '</pre>\n'
    try:
        tmpl = open('ansi.html').read()
        out = tmpl.replace('<body>', '<body>'+body)
    except FileNotFoundError:
        out = body

    with p.open_text(mode='w') as fp:
        fp.write(out)


class DrawingSheet(JsonSheet):
    rowtype='strings'  # rowdef: { .x, .y, .text, .color, .group, .layer }
    columns=[
        ItemColumn('t', type=float),
        ItemColumn('x', type=int),
        ItemColumn('y', type=int),
        ItemColumn('text'),
        ItemColumn('color'),
        ItemColumn('group'),
        ItemColumn('tags'),
    ]
    def newRow(self):
        return AttrDict(x=None, y=None, text='', color='', tags=[])

    def addRow(self, row, **kwargs):
        row = super().addRow(row, **kwargs)
        vd.addUndo(self.rows.remove, row)
        return row

    @drawcache_property
    def groups(self):
        return {r.group+'.':r for r in self.rows if not r.group.endswith('.')}

    def group_selected(self, gname):
        nr = self.newRow()
        nr.rows = self.selectedRows
        x1, y1, x2, y2 = bounding_box(nr.rows)
        nr.x, nr.y, nr.w, nr.h = x1, y1, x2-x1, y2-y1
        nr.group = gname

        for r in nr.rows:
            r.group = gname + '.' + r.get('group', '')
            r.x -= x1
            r.y -= y1

        self.deleteSelected()
        nr = self.addRow(nr)
        self.select([nr])
        vd.status('group "%s" (%d objects)' % (gname, self.nSelectedRows))

    def regroup_selected(self):
        regrouped = []
        groups = set()  # that items were grouped into
        for r in self.someSelectedRows:
            if r.group and r.group.endswith('.'):
                regrouped.append(r)
                g = self.groups[r.group]
                g.rows.append(r)
                groups.add(r.group)

        self.deleteBy(lambda r,rows=regrouped: r in rows)
        self.select(list(g for name, g in self.groups.items() if name in groups))

        vd.status('regrouped %d %s' % (len(regrouped), self.rowtype))

    def degroup_selected(self):
        degrouped = []
        groups = set()
        for r, x, y, top in iterdeep(self.someSelectedRows):
            r.x = x
            r.y = y
            if r.rows:
                groups.add(r.group)
            else:
                self.addRow(r)
                degrouped.append(r)

        for g in groups:
            self.groups[g+'.'].rows.clear()

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
    def iterbox(self, x, y, w, h):
        'Yield rows within the given box.'
        for nx in range(x, x+w):
            for ny in range(y, y+h):
                yield from self.drawing[(nx,ny)]

    @property
    def rows(self):
        return self.source.rows

    @rows.setter
    def rows(self, v):
        pass #        self.source.rows = v

    def __getattr__(self, k):
        return getattr(self.source, k)

    def commandCursor(self, execstr):
        if 'cursor' in execstr:
            return '%s %s' % (self.cursorX, self.cursorX+self.cursorW), '%s %s' % (self.cursorY, self.cursorY+self.cursorH)
        return '', ''

    def moveToRow(self, rowstr):
        self.refresh()
        a, b = map(int, rowstr.split())
        self.cursorY, self.cursorH = min(a,b), abs(b-a)
        return True

    def moveToCol(self, colstr):
        self.refresh()
        a, b = map(int, colstr.split())
        self.cursorX, self.cursorW = min(a,b), abs(b-a)
        return True

    def itercursor(self):
        return self.iterbox(self.cursorX, self.cursorY, self.cursorW+1, self.cursorH+1)

    def within_cursor(self, x, y, w, h):
        if x+w-1 < self.cursorX: return False
        if y+h-1 < self.cursorY: return False
        if y > self.cursorY+self.cursorH: return False
        if x > self.cursorX+self.cursorW: return False
        return True

    def refresh(self):
        self._scr = mock.MagicMock(__bool__=mock.Mock(return_value=False))
        self.draw(self._scr)

    def draw(self, scr):
        self.drawing = defaultdict(list)  # (x, y) -> list of rows; actual screen layout (topmost last in list)
        self._tags = defaultdict(list)  # "groupname" -> list of rows in that group

        t = vd.fixed_t if vd.fixed_t is not None else (time.time() - vd.first_t)
        selectedGroups = set()  # any group with a selected element

        # draw blank cursor as backdrop
        for i in range(self.cursorH+1):
            for j in range(self.cursorW+1):
                clipdraw(scr, self.cursorY+i, self.cursorX+j, ' ', colors.color_current_row)

        self.minX, self.minY, self.maxX, self.maxY = xmin, ymin, xmax, ymax = bounding_box(self.source.rows)

        for row, x, y, toprow in iterdeep(self.source.rows):
            r = AttrDict(row)
            rtags = r.tags
            for g in rtags:
                self._tags[g].append(row)

            if r.text and not any_match(rtags, self.disabled_tags):
                if 0 <= y < self.windowHeight-1 and 0 <= x < self.windowWidth:  # inside screen
                    c = r.color
                    if r.t is not None:
                        if r.t > t:
                            continue
                    if self.within_cursor(x, y, r.w or dispwidth(r.text), r.h or 1):
                        c = self.options.color_current_row + ' ' + c
                    if self.source.isSelected(toprow):
                        c = self.options.color_selected_row + ' ' + c
                        selectedGroups |= set(rtags)
                    a = colors[c]
                    w = clipdraw(scr, y, x, r.text, a)
                    for i in range(0, w):
                        cellrows = self.drawing[(x+i, y)]
                        if toprow not in cellrows:
                            cellrows.append(toprow)

        if self.options.visibility > 0:
            defattr = self.options.color_default
            clipdraw(scr, i+1, self.windowWidth-20, '00: (reset)', defattr)
            for i, tag in enumerate(self._tags.keys()):
                c = defattr
                if tag in self.disabled_tags:
                    c = self.options.color_graph_hidden
                if self.cursorRow and tag in self.cursorRow.get('group', ''):
                    c = self.options.color_current_row + ' ' + c
                if tag in selectedGroups:
                    c = self.options.color_selected_row + ' ' + c
                clipdraw(scr, i+1, self.windowWidth-20, '%02d: %s' % (i+1, tag), colors[c])

        self.last_t = t

    def reload(self):
        self.source.ensureLoaded()

    def place_text(self, text, x=None, y=None, dx=0, dy=0):
        'Return (width, height) of drawn text.'
        if x is None: x = self.cursorX
        if y is None: y = self.cursorY
        r = AttrDict(x=x, y=y, text=text, color='')
        self.source.addRow(r)
        self.modified = True
        self.go_forward(dispwidth(text)+dx, 1+dy)
        if self.cursorX > self.windowWidth:
            self.cursorX = 1
            self.cursorY += 1
        if self.cursorY > self.windowHeight-1:
            self.cursorX += 1
            self.cursorY = 1

    def get_text(self, x=None, y=None):
        'Return text of topmost visible element at (x,y) (or cursor if not given).'
        if x is None: x = self.cursorX
        if y is None: y = self.cursorY
        r = self.drawing.get((x,y), None)
        if not r: return ''
        return r[-1]['text']

    def remove_at(self, x, y, w, h):
        rows = list(self.iterbox(x, y, w+1, h+1))
        self.source.deleteBy(lambda r,rows=rows: r in rows)
        return rows

    @property
    def cursorRows(self):
        return self.drawing[(self.cursorX, self.cursorY)]

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
        if cr.group:
            n = len(list(iterdeep(cr.rows)))
            return '%s (%s objects)' % (cr.group, n)
        return '???'

    @property
    def cursorCharName(self):
        return unicodedata.name(self.cursorChar[0])

    def go_left(self):
        if self.options.pen_down:
            self.pendir = 'l'
            self.place_text(ch, self.cursorX, self.cursorY, **vd.memo_chars[0])
        else:
            self.cursorX -= 1

    def go_right(self):
        if self.options.pen_down:
            self.pendir = 'r'
            self.place_text(ch, self.cursorX, self.cursorY, **vd.memo_chars[0])
        else:
            self.cursorX += 1

    def go_down(self):
        if self.options.pen_down:
            self.pendir = 'd'
            self.place_text(ch, self.cursorX, self.cursorY, **vd.memo_chars[0])
        else:
            self.cursorY += 1

    def go_up(self):
        if self.options.pen_down:
            self.pendir = 'u'
            self.place_text(ch, self.cursorX, self.cursorY, **vd.memo_chars[0])
        else:
            self.cursorY -= 1

    def go_pagedown(self, n):
        self.cursorY = self.windowHeight-2

    def go_leftmost(self):
        self.cursorX = 0

    def go_rightmost(self):
        self.cursorX = self.maxX

    def go_top(self):
        self.cursorY = 0

    def go_bottom(self):
        self.cursorY = self.maxY

    def go_forward(self, x, y):
        if self.pendir == 'd': self.cursorY += y
        elif self.pendir == 'u': self.cursorY -= y
        elif self.pendir == 'r': self.cursorX += x
        elif self.pendir == 'l': self.cursorX -= x

    def slide_selected(self, dx, dy):
        for r in self.source.someSelectedRows:
            r['x'] += dx
            r['y'] += dy

    def go_obj(self, xdir=0, ydir=0):
        x=self.cursorX
        y=self.cursorY
        currows = self.drawing.get((x, y), [])
        xmin = min(x for x, y in self.drawing.keys())
        ymin = min(y for x, y in self.drawing.keys())
        xmax = max(x for x, y in self.drawing.keys())
        ymax = max(y for x, y in self.drawing.keys())

        while xmin <= x <= xmax and ymin <= y <= ymax:
            for r in self.drawing.get((x, y), [])[::-1]:
                if r and r not in currows:
                    self.cursorX = x
                    self.cursorY = y
                    return
            x += xdir
            y += ydir

    def checkCursor(self):
        self.cursorX = min(self.windowWidth-2, max(0, self.cursorX))
        self.cursorY = min(self.windowHeight-2, max(0, self.cursorY))

    def end_cursor(dwg, x, y):
        dwg.cursorW=abs(x-dwg.cursorX)
        dwg.cursorH=abs(y-dwg.cursorY)
        if x < dwg.cursorX:
            dwg.cursorX -= dwg.cursorH
        if y < dwg.cursorY:
            dwg.cursorY -= dwg.cursorW

    def join_rows(dwg, rows):
        vd.addUndo(setattr, rows[0], 'text', rows[0].text)
        rows[0].text = ''.join(r.text for r in rows)
        dwg.source.deleteBy(lambda r,rows=rows[1:]: r in rows)

    def paste_chars(dwg, charslist):
        p = charslist[0]
        newrows = deepcopy(charslist)
        x = dwg.cursorX-p.get('x', dwg.cursorX)
        y = dwg.cursorY-p.get('y', dwg.cursorY)
        for r in adj_xy(x, y, newrows):
            dwg.source.addRow(r)

        if dwg.source.nSelectedRows == 0: # auto-select newly pasted item
            dwg.source.select(newrows)

    def select_tag(self, tag):
        self.select(list(r for r in self.source.rows if tag in (r.tags or '')))

    def unselect_tag(self, tag):
        self.unselect(list(r for r in self.rows if tag in (r.tags or '')))

    def align_selected(self, attrname):
        rows = self.someSelectedRows
        for r in rows:
            r.x = rows[0].x


Drawing.init('cursorX', lambda: 0)
Drawing.init('cursorY', lambda: 0)
Drawing.init('cursorW', lambda: 0)
Drawing.init('cursorH', lambda: 0)
Drawing.init('drawing', dict)  # (x,y) -> list of rows
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

Drawing.addCommand('BUTTON1_PRESSED', 'move-cursor', 'sheet.cursorX=mouseX; sheet.cursorY=mouseY; sheet.cursorW=1; sheet.cursorH=1', 'start cursor box with left mouse button press')
Drawing.addCommand('BUTTON1_RELEASED', 'end-cursor', 'end_cursor(mouseX, mouseY)', 'end cursor box with left mouse button release')

Drawing.addCommand('', 'align-x-selected', 'align_selected("x")')

Drawing.addCommand('gKEY_HOME', 'slide-top-selected', 'source.slide_top(source.someSelectedRows, -1)', 'move selected items to top layer of drawing')
Drawing.addCommand('gKEY_END', 'slide-bottom-selected', 'source.slide_top(source.someSelectedRows, 0)', 'move selected items to bottom layer of drawing')
Drawing.addCommand('d', 'delete-cursor', 'remove_at(cursorX, cursorY, cursorW, cursorH); go_forward(1, 1)', 'delete first item under cursor')
Drawing.addCommand('gd', 'delete-selected', 'source.deleteSelected()')
Drawing.addCommand('a', 'add-input', 'place_text(input("text: ", value=get_text()), dx=1)')
Drawing.addCommand('e', 'edit-char', 'cursorRow.text=input("text: ", value=get_text())')
Drawing.addCommand('ge', 'edit-selected', 'v=input("text: ", value=get_text())\nfor r in source.selectedRows: r.text=v')
Drawing.addCommand('y', 'yank-char', 'p=AttrDict(cursorRow); vd.memo_chars=adj_xy(-p.x, -p.y, [p])')
Drawing.addCommand('gy', 'yank-selected', 'sel=[AttrDict(r) for r in source.selectedRows]; vd.memo_chars=adj_xy(-sel[0].x, -sel[0].y, sel)')
Drawing.addCommand('x', 'cut-char', 'vd.memo_chars=remove_at(cursorX, cursorY, cursorW, cursorH)')
Drawing.addCommand('zx', 'cut-char-top', 'r=list(itercursor())[-1]; vd.memo_chars=[r]; source.deleteBy(lambda r,row=r: r is row)')
Drawing.addCommand('p', 'paste-chars', 'paste_chars(vd.memory.cliprows[2])')
Drawing.addCommand('gp', 'paste-chars-selected', 'paste_chars(vd.memory.cliprows[2], selectedRows)', 'paste characters from clipboard over selection')

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

Drawing.addCommand('00', 'enable-all-groups', 'disabled_tags.clear()')
for i in range(1, 99):
    Drawing.addCommand('%02d'%i, 'toggle-group-%s'%i, 'g=list(_tags.keys())[%s]; disabled_tags.remove(g) if g in disabled_tags else disabled_tags.add(g)' %(i-1))
    Drawing.addCommand('g%02d'%i, 'select-group-%s'%i, 'g=list(_tags.keys())[%s]; source.select(source.gatherTag(g))' %(i-1))
    Drawing.addCommand('z%02d'%i, 'unselect-group-%s'%i, 'g=list(_tags.keys())[%s]; source.unselect(source.gatherTag(g))' %(i-1))


BaseSheet.addCommand('A', 'new-drawing', 'vd.push(Drawing("untitled", source=DrawingSheet("", source=Path("untitled.ddw"))))')
BaseSheet.addCommand('M', 'open-unicode', 'vd.push(vd.unibrowser)')
BaseSheet.addCommand('`', 'push-source', 'vd.push(sheet.source)')

DrawingSheet.addCommand('^G', 'show-char', 'status(f"{sheet.cursorCharName}")')
DrawingSheet.addCommand(ENTER, 'dive-group', 'cursorRow.rows or fail("not a group"); vd.push(DrawingSheet(source=sheet, rows=cursorRow.rows))')
DrawingSheet.addCommand('g'+ENTER, 'dive-selected', 'ret=sum(((r.rows or []) for r in selectedRows), []) or fail("no groups"); vd.push(DrawingSheet(source=sheet, rows=ret))')
Drawing.addCommand('&', 'join-selected', 'join_rows(source.selectedRows)')

@Drawing.command('gm', 'tag-selected', '')
def tag_selected(sheet):
    tagstr = vd.input('tag selected as: ', type='tag')
    tags = tagstr.split()
    for r in sheet.someSelectedRows:
        for tag in tags:
            if tag not in (r.tags or ''):
                r.tags.append(tag)

Drawing.addCommand(ENTER, 'dive-cursor', 'vd.push(DrawingSheet(source=sheet, rows=cursorRows))')
Drawing.addCommand('g'+ENTER, 'dive-selected', 'vd.push(DrawingSheet(source=sheet, rows=source.selectedRows))')
Drawing.addCommand('{', 'go-prev-selected', 'source.moveToNextRow(lambda row,source=source: source.isSelected(row), reverse=True) or fail("no previous selected row"); sheet.cursorX=source.cursorRow.x; sheet.cursorY=source.cursorRow.y', 'go to previous selected row'),
Drawing.addCommand('}', 'go-next-selected', 'source.moveToNextRow(lambda row,source=source: source.isSelected(row)) or fail("no next selected row"); sheet.cursorX=source.cursorRow.x; sheet.cursorY=source.cursorRow.y', 'go to next selected row'),
Drawing.addCommand('z'+ENTER, 'dive-cursor-group', 'vd.push(DrawingSheet(source=sheet, rows=rows_by_group(cursorRow["group"])))')
Drawing.addCommand('z^Y', 'pyobj-cursor', 'vd.push(PyobjSheet("cursor_top", source=cursorRow))')
Drawing.addCommand('^Y', 'pyobj-cursor', 'vd.push(PyobjSheet("cursor", source=cursorRows))')

Drawing.addCommand('^S', 'save-sheet', 'vd.saveSheets(inputPath("save to: ", value=source.getDefaultSaveName()), sheet.source, confirm_overwrite=options.confirm_overwrite)', 'save current drawing')
Drawing.addCommand('i', 'insert-row', 'for r in source.someSelectedRows: r.y += (r.y >= cursorY)', '')
Drawing.addCommand('zi', 'insert-col', 'for r in source.someSelectedRows: r.x += (r.x >= cursorX)', '')

Drawing.addCommand('zm', 'place-mark', 'sheet.mark=(cursorX, cursorY)')
Drawing.addCommand('m', 'swap-mark', '(cursorX, cursorY), sheet.mark=sheet.mark, (cursorX, cursorY)')
Drawing.addCommand('v', 'visibility', 'options.visibility ^= 1')
Drawing.addCommand('r', 'reset-time', 'vd.first_t=time.time()')
Drawing.addCommand('>', 'time-next', 'vd.fixed_t += 1')
Drawing.addCommand('<', 'time-prev', 'vd.fixed_t -= 1')

Drawing.addCommand('kRIT5', 'resize-cursor-wider', 'sheet.cursorW += 1')
Drawing.addCommand('kLFT5', 'resize-cursor-thinner', 'sheet.cursorW -= 1')
Drawing.addCommand('kUP5', 'resize-cursor-shorter', 'sheet.cursorH -= 1')
Drawing.addCommand('kDN5', 'resize-cursor-taller', 'sheet.cursorH += 1')

Drawing.bindkey('zKEY_RIGHT', 'resize-cursor-wider')
Drawing.bindkey('zKEY_LEFT', 'resize-cursor-thinner')
Drawing.bindkey('zKEY_UP', 'resize-cursor-shorter')
Drawing.bindkey('zKEY_DOWN', 'resize-cursor-taller')

Drawing.bindkey('C', 'open-colors')

Drawing.init('mark', lambda: (0,0))
Drawing.class_options.disp_rstatus_fmt='{sheet.pendir}  <{sheet.cursorDesc}> {sheet.options.disp_selected_note}{sheet.source.nSelectedRows}'
Drawing.class_options.quitguard='modified'
Drawing.class_options.null_value=''
Drawing.class_options.quitguard=True
DrawingSheet.class_options.null_value=''
