import curses
import functools
from copy import copy

from visidata import options, Extensible, drawcache, drawcache_property, VisiData
import visidata
from collections import namedtuple

__all__ = ['ColorAttr', 'colors', 'update_attr', 'ColorMaker']


ColorAttr = namedtuple('ColorAttr', ('color', 'attributes', 'precedence', 'attr'))


def update_attr(oldattr, updattr, updprec=None):
    if isinstance(updattr, ColorAttr):
        if updprec is None:
            updprec = updattr.precedence
        updcolor = updattr.color
        updattr = updattr.attributes
    else:
        updcolor = updattr & curses.A_COLOR
        updattr = updattr & ~curses.A_COLOR
        if updprec is None:
            updprec = 0

    # starting values, work backwards
    newcolor = oldattr.color
    newattr = oldattr.attributes | updattr
    newprec = oldattr.precedence

    if not newcolor or updprec > newprec:
        if updcolor:
            newcolor = updcolor
        newprec = updprec

    return ColorAttr(newcolor, newattr, newprec, newcolor | newattr)


class ColorMaker:
    def __init__(self):
        self.color_pairs = {}  # (fg,bg) -> (color_attr, colornamestr) (can be or'ed with other attrs)
        self.default_fgbg = (-1, -1)  # default fg and bg

    @drawcache_property
    def colorcache(self):
        return {}

    def setup(self):
        if options.use_default_colors:
            curses.use_default_colors()
            self.default_fgbg = (-1, -1)
        else:
            self.default_fgbg = (-1, curses.COLOR_BLACK)

    @VisiData.cached_property
    def colors(self):
        'not computed until curses color has been initialized'
        return {x[6:]:getattr(curses, x) for x in dir(curses) if x.startswith('COLOR_') and x != 'COLOR_PAIRS'}

    def __getitem__(self, colornamestr):
        return self._colornames_to_cattr(colornamestr).attr

    def __getattr__(self, optname):
        'colors.color_foo returns colors[options.color_foo]'
        return self.get_color(optname).attr

    @drawcache
    def resolve_colors(self, colorstack):
        'Returns the ColorAttr for the colorstack, a list of color option names sorted highest-precedence color first.'
        cattr = ColorAttr(0,0,0,0)
        for coloropt in colorstack:
            c = self.get_color(coloropt)
            cattr = update_attr(cattr, c)
        return cattr

    def _colornames_to_cattr(self, colornamestr, precedence=0):
        attrs = 0
        fgbg = list(self.default_fgbg)
        i = 0
        for x in colornamestr.split():
            if x == 'fg':
                i = 0
                continue
            elif x in ['on', 'bg']:
                i = 1
                continue

            attr = getattr(curses, 'A_' + x.upper(), None)
            if attr:
                attrs |= attr
            else:
                if fgbg[i] == self.default_fgbg[i]:  # keep first known color
                    fgbg[i] = int(x) if x.isdigit() else self.colors.get(x.upper(), 0)

        if tuple(fgbg) == tuple(self.default_fgbg):
            color = 0
        else:
            pairnum, _ = self.color_pairs.get(tuple(fgbg), (None, ''))
            if pairnum is None:
                pairnum = len(self.color_pairs)+1
                try:
                    curses.init_pair(pairnum, *fgbg)
                except curses.error as e:
                    return ColorAttr(0, attrs, precedence, attrs)
                self.color_pairs[tuple(fgbg)] = (pairnum, colornamestr)

            color = curses.color_pair(pairnum)
        return ColorAttr(color, attrs, precedence, color | attrs)

    def get_color(self, optname, precedence=0):
        'colors.color_foo returns colors[options.color_foo]'
        r = self.colorcache.get(optname, None)
        if r is None:
            coloropt = options._get(optname)
            colornamestr = coloropt.value if coloropt else optname
            r = self.colorcache[optname] = self._colornames_to_cattr(colornamestr, precedence)
        return r

colors = ColorMaker()
