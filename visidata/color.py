import curses
import functools
from copy import copy
from collections import namedtuple
from dataclasses import dataclass

from visidata import vd, options, Extensible, drawcache, drawcache_property, VisiData
import visidata

__all__ = ['ColorAttr', 'colors', 'update_attr', 'ColorMaker', 'rgb_to_attr']

vd.help_color = '''Color syntax: `<attribute> <fg-color> on <bg-color>`

- attributes: [:bold]bold[/] [:underline]underline[/] [:italic]italic[/] [:reverse]reverse[/]
- colors: 0-255 or [:black on 238]black[/] [:red on 238]red[/] [:green on 238]green[/] [:yellow on 238]yellow[/] [:blue on 238]blue[/] [:magenta on 238]magenta[/] [:cyan on 238]cyan[/] [:white on 238]white[/]
- the second color is used as a fallback if the first color is not available

See [:onclick https://visidata.org/docs/colors]https://visidata.org/docs/colors[/] for more detailed info.
'''


@dataclass
class ColorAttr:
    fg:int = -1         # default is no foreground specified
    bg:int = -1         # default is no background specified
    attributes:int = 0       # default is no attributes
    precedence:int = 0  # default is lowest priority
    colorname:str = ''

    def __init__(self, fg:int=-1, bg:int=-1, attributes:int=0, precedence:int=0, colorname:str=''):
        assert fg < 256, fg
        assert bg < 256, bg
        self.fg = fg
        self.bg = bg
        self.attributes = attributes
        self.precedence = precedence
        self.colorname = colorname

    def update(self, b:'ColorAttr', prec:int=10) -> 'ColorAttr':
        return update_attr(self, b, prec)

    @property
    def attr(self) -> int:
        a = colors._get_colorpair(self.fg, self.bg, self.colorname) | self.attributes
        assert a >= 0, a
        return a

    def as_str(self) -> str:
        attrnames = [attrname for attrname, attr in colors._attrs.items() if self.attributes & attr]
        attrnames.append(f'{self.fg} on {self.bg}')
        return ' '.join(attrnames)


def update_attr(oldattr:ColorAttr, updattr:ColorAttr, updprec:int=None) -> ColorAttr:
    assert isinstance(updattr, ColorAttr), updattr
    if updprec is None:
        updprec = updattr.precedence
    updfg = updattr.fg
    updbg = updattr.bg
    updattr = updattr.attributes

    # starting values, work backwards
    newfg = oldattr.fg
    newbg = oldattr.bg
    newattr = oldattr.attributes | updattr
    newprec = oldattr.precedence

    if newfg < 0 or (updfg >= 0 and updprec > newprec):
        newfg = updfg
    if newbg < 0 or (updbg >= 0 and updprec > newprec):
        newbg = updbg

    newprec = max(updprec, newprec)

    return ColorAttr(newfg, newbg, newattr, newprec)


class ColorMaker:
    def __init__(self):
        self.color_pairs = {}  # (fg,bg) -> (pairnum, colornamestr) (pairnum can be or'ed with other attrs)
        self.color_cache = {}  # colorname -> colorpair

    @drawcache_property
    def colorcache(self):
        return {}

    def setup(self):
        try:
            curses.use_default_colors()
        except Exception as e:
            pass

    @drawcache_property
    def colors(self):
        'not computed until curses color has been initialized'
        return {x[6:]:getattr(curses, x) for x in dir(curses) if x.startswith('COLOR_') and x != 'COLOR_PAIRS'}

    def __getitem__(self, colorname:str) -> ColorAttr:
        'colors["green"] or colors["foo"] returns parsed ColorAttr.'
        return self.get_color(colorname)

    def __getattr__(self, optname) -> ColorAttr:
        'colors.color_foo or colors.foo returns parsed ColorAttr.'
        return self.get_color(optname)

    @drawcache
    def resolve_colors(self, colorstack):
        'Returns the ColorAttr for the colorstack, a list of (prec, color_option_name) sorted highest-precedence color first.'
        cattr = ColorAttr()
        for prec, coloropt in colorstack:
            c = self.get_color(coloropt)
            cattr = update_attr(cattr, c, prec)
        return cattr

    def get_color(self, optname:str, precedence:int=0) -> ColorAttr:
        '''Return ColorAttr for options.color_foo if *optname* of either "foo" or "color_foo",
           Otherwise parse *optname* for colorstring like "bold 34 red on 135 blue".'''
        r = self.colorcache.get(optname, None)
        if r is None:
            coloropt = vd.options._get(optname) or vd.options._get(f'color_{optname}')
            colornamestr = coloropt.value if coloropt else optname
            r = self.colorcache[optname] = self._colornames_to_cattr(colornamestr, precedence)
        return r

    def _split_colorstr(self, colorstr):
        'Return (fgstr, bgstr, attrlist) parsed from colorstr.'
        fgbgattrs = ['', '', []]  # fgstr, bgstr, attrlist
        if not colorstr:
            return fgbgattrs
        colorstr = str(colorstr)

        i = 0  # fg by default
        for x in colorstr.split():
            if x == 'fg':
                i = 0
                continue
            elif x in ['on', 'bg']:
                i = 1
                continue

            if hasattr(curses, 'A_' + x.upper()):
                fgbgattrs[2].append(x)
            else:
                if not fgbgattrs[i]:  # keep first known color
                    if self._get_colornum(x) is not None:   # only set known colors
                        fgbgattrs[i] = x
                    else:
                        fgbgattrs[i] = None

        return fgbgattrs

    def _get_colornum(self, colorname:'str|int', default:int=-1) -> int:
        'Return terminal color number for colorname.'
        if isinstance(colorname, int):
            return colorname

        if not colorname:
            return default

        r = self.color_cache.get(colorname, None)
        if r is not None:
            return r

        try:
            r = int(colorname)
        except Exception:
            r = self.colors.get(colorname.upper())

        if r is None:
            return None

        try: # test to see if color is available
            curses.init_pair(255, r, 0)
            self.color_cache[colorname] = r
            return r
        except curses.error as e:
            return None  # not available
        except ValueError:  # Python 3.10+  issue #1227
            return None

    def _attrnames_to_num(self, attrnames:'list[str]') -> int:
        attrs = 0
        for attr in attrnames:
            attrs |= getattr(curses, 'A_'+attr.upper())
        return attrs

    @drawcache_property
    def _attrs(self):
        return {k[2:].lower():getattr(curses, k) for k in dir(curses) if k.startswith('A_') and k != 'A_ATTRIBUTES'}

    @drawcache
    def _colornames_to_cattr(self, colorname:str, precedence=0) -> ColorAttr:
        fg, bg, attrlist = self._split_colorstr(colorname)

        fg = self._get_colornum(fg)
        bg = self._get_colornum(bg)
        return ColorAttr(fg, bg,
                         self._attrnames_to_num(attrlist),
                         precedence, colorname)

    def _get_colorpair(self, fg:'int|None', bg:'int|None', colorname:str) -> int:
            pairnum, _ = self.color_pairs.get((fg, bg), (None, ''))
            if pairnum is None:
                if len(self.color_pairs) > 254:
                    self.color_pairs.clear()  # start over
                    self.color_cache.clear()
                pairnum = len(self.color_pairs)+1
                if fg is None: fg = -1
                if bg is None: bg = -1
                try:
                    curses.init_pair(pairnum, fg, bg)
                except curses.error as e:
                    return 0  # do not cache
                self.color_pairs[(fg, bg)] = (pairnum, colorname)

            return curses.color_pair(pairnum)


colors = ColorMaker()

def rgb_to_xterm256(r:int,g:int,b:int,a:int=255) -> int:
    if a == 0:
        return -1

    if max(r,g,b) - min(r,g,b) < 8:
        if r <= 4: return 16
        elif r <= 8: return 232
        elif r >= 247: return 231
        elif r >= 238: return 255
        else:
            return int(232 + (r-8)//10)
    else:
        r = max(0, r-(95-40)) // 40
        g = max(0, g-(95-40)) // 40
        b = max(0, b-(95-40)) // 40
        return int(16 + r*36 + g*6 + b)


@functools.lru_cache(256)
def rgb_to_attr(r:int,g:int,b:int,a:int=255) -> str:
    return str(rgb_to_xterm256(r,g,b,a))


import sys
vd.addGlobals({k:getattr(sys.modules[__name__], k) for k in __all__})
