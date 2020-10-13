import curses
import functools
from copy import copy

from visidata import options, Extensible, drawcache, drawcache_property
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
        self.attrs = {}
        self.color_attrs = {}

    @drawcache_property
    def colorcache(self):
        return {}

    def setup(self):
        if options.use_default_colors:
            curses.use_default_colors()
            default_bg = -1
        else:
            default_bg = curses.COLOR_BLACK

        self.color_attrs['black'] = curses.color_pair(0)

        for c in range(0, options.force_256_colors and 256 or curses.COLORS):
            try:
                curses.init_pair(c+1, c, default_bg)
                self.color_attrs[str(c)] = curses.color_pair(c+1)
            except curses.error as e:
                pass # curses.init_pair gives a curses error on Windows

        for c in 'red green yellow blue magenta cyan white'.split():
            colornum = getattr(curses, 'COLOR_' + c.upper())
            self.color_attrs[c] = curses.color_pair(colornum+1)

        for a in 'normal blink bold dim reverse standout underline'.split():
            self.attrs[a] = getattr(curses, 'A_' + a.upper())

    def keys(self):
        return list(self.attrs.keys()) + list(self.color_attrs.keys())

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
        color, attr = 0, 0
        for colorname in colornamestr.split(' '):
            if colorname in self.color_attrs:
                if not color:
                    color = self.color_attrs[colorname.lower()]
            elif colorname in self.attrs:
                attr = self.attrs[colorname.lower()]
        return ColorAttr(color, attr, precedence, color | attr)

    def get_color(self, optname, precedence=0):
        'colors.color_foo returns colors[options.color_foo]'
        r = self.colorcache.get(optname, None)
        if r is None:
            coloropt = options._get(optname)
            colornamestr = coloropt.value if coloropt else optname
            r = self.colorcache[optname] = self._colornames_to_cattr(colornamestr, precedence)
        return r

colors = ColorMaker()
