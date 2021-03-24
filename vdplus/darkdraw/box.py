import itertools
import curses

from visidata import vd, colors
from wcwidth import wcswidth

def wc_rjust(text, length, padding=' '):
    return padding * max(0, (length - wcswidth(text))) + text

def wc_center(text, length, padding=' '):
    x = max(0, (length - wcswidth(text)))
    return padding*(x//2) + text + padding*((x+1)//2)

def wc_ljust(text, length, padding=' '):
    return text + padding * max(0, (length - wcswidth(text)))


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


class DrawableBox(CharBox):
    def reverse(self):
        if not self.scr: return
        for y in range(self.y1, self.y2):
            for x in range(self.x1, self.x2):
                try:
                    self.scr.chgat(y, x, 1, screen_contents.get((x,y), (0,0))[1] | curses.A_REVERSE)
                except curses.error:
                    vd.fail(y, x)

    def erase(self):
#        screen_contents.clear()
        for y in range(self.y1, self.y2):
            self.scr.addstr(y, 0, ' '*self.w, 0)

    def draw(self, yr, xr, s, attr=0):
        'Draw *s* into box.  *yr* an *xr* in relative coordinates; may be ranges.'
        if isinstance(attr, str):
            attr = colors.get(attr)

        if not isinstance(yr, range): yr = range(yr, yr+1)
        if not isinstance(xr, range): xr = range(xr, xr+1)
        ymax, xmax = self.scr.getmaxyx()
        if self.y1+max(yr) > ymax: fail('need taller screen (at least %s)' % max(yr))
        if self.x1+max(xr) > xmax: fail('need wider screen (at least %s)' % max(xr))
        for y in yr:
            for x in xr:
                screen_contents[(self.x1+x, self.y1+y)] = (s, attr)
                self.scr.addstr(self.y1+y, self.x1+x, s, attr)

    def box(self, x1=0, y1=0, dx=0, color=''):
        if self.w <= 0 or self.h <= 0: return
        attr = colors.get(color)
        x2, y2=x1+self.w+1, y1+self.h+1
        self.draw(0, range(x1, x2), '━', attr)
        self.draw(y2, range(x1, x2), '━', attr)
        self.draw(range(y1, y2), x1, '┃', attr)
        self.draw(range(y1, y2), x2, '┃', attr)
        self.draw(y1, x1, '┏', attr)
        self.draw(y1, x2, '┓', attr)
        self.draw(y2, x1, '┗', attr)
        self.draw(y2, x2, '┛', attr)
        if dx:
            self.draw(y1, range(x1+dx, x2, dx), '┯', attr)
            self.draw(y1, range(x1+dx, x2, dx), '┯', attr)
            self.draw(range(y1+1, y2), range(x1+dx, x2, dx), '│', attr)
            self.draw(y2, range(x1+dx, x2, dx), '┷', attr)

    def rjust(self, s, x=0, y=0, w=0, color=' '):
        w = w or self.w
        return self.ljust(s, x=self.x1+x+w-wcswidth(s)-1, y=y, color=color)

    def center(self, s, x=0, y=0, w=0, padding=' '):
        x += max(0, ((w or self.w) - wcswidth(s)))
        return self.ljust(s, x=self.x1+x//2, y=y, w=w-x)

    def ljust(self, s, x=0, y=0, w=0, color=' '):
        if self.w <= 0 or self.h <= 0: return
        if y > self.h: fail(f'{y}/{self.h}')

        scrh, scrw = self.scr.getmaxyx()
        attr = colors.get(color)
        pre = ''
        xi = x
        for c in s:
            cw = wcswidth(c)
            if xi+cw >= self.w:
                break
            if cw == 0:
                pre += c
            elif cw < 0: # not printable
                pass
            else:
                self.draw(y, xi, pre+c, attr)
                pre = ''
                xi += cw

        # add blanks to fill width
        for i in range(xi-x, w+1):
            self.draw(y, xi+i, ' ', attr)

        return w or xi-x

    def blit(self, tile, *, y1=0, x1=0, y2=None, x2=None, xoff=0, yoff=0):
        y2 = y2 or self.h-1
        x2 = x2 or self.w-1
        y = y1
        lines = list(itertools.zip_longest(tile.lines, tile.pcolors))
        while y-y1+yoff < 0 and y < y2:
            self.draw(y, x1, ' '*(x2-x1), 0)
            y += 1

        while y < y2:
            if y-y1+yoff >= len(lines):
                self.draw(y, x1, ' '*(x2-x1), 0)
                y += 1
                continue

#            line, linemask = lines[(y-y1+yoff)%len(lines)]
            line, linemask = lines[y-y1+yoff]
            pre = ''
            x = x1
            i = 0
            while x-x1+xoff < 0 and x < x2:
                self.draw(y, x1, ' '*(x2-x1), 0)
                x += 1

            while x < x2:
                if x-x1+xoff >= len(line):
                    self.draw(y, x, ' '*(x2-x), 0)
                    break
#                c = line[(xoff+i)%len(line)]
                c = line[x-x1+xoff]
                cmask = linemask[x-x1+xoff] if linemask else 0
                w = wcswidth(c)
                if w == 0:
                    pre = c
                elif w < 0: # not printable
                    pass
                else:
                    attr = colors.get(tile.palette[cmask]) if cmask else 0
                    try:
                        self.draw(y, x, pre+c, attr)
                    except curses.error:
                        raise Exception(f'y={y} x={x}')
                    x += w
                    pre = ''
                i += 1

            y += 1

        while y < y2:
          try:
            self.draw(y, x1, ' '*(x2-x1), 0)
            y += 1
          except curses.error:
              raise Exception(y, y2)
