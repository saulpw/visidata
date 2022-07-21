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
        self.color_cache = {}  # colorname -> colorpair

    @drawcache_property
    def colorcache(self):
        return {}

    def setup(self):
        curses.use_default_colors()

    @drawcache_property
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
        'Returns the ColorAttr for the colorstack, a list of (prec, color_option_name) sorted highest-precedence color first.'
        cattr = ColorAttr(0,0,0,0)
        for prec, coloropt in colorstack:
            c = self.get_color(coloropt)
            cattr = update_attr(cattr, c, prec)
        return cattr

    def split_colorstr(self, colorstr):
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

        return fgbgattrs

    def _get_colornum(self, colorname, default=-1):
        'Return terminal color number for colorname.'
        if not colorname: return default
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

    @drawcache
    def _colornames_to_cattr(self, colornamestr, precedence=0):
        fg, bg, attrlist = self.split_colorstr(colornamestr)
        attrs = 0
        for attr in attrlist:
            attrs |= getattr(curses, 'A_'+attr.upper())

        if not fg and not bg:
            color = 0
        else:
            deffg, defbg, _ = self.split_colorstr(options.color_default)
            fgbg = (self._get_colornum(fg, self._get_colornum(deffg)),
                    self._get_colornum(bg, self._get_colornum(defbg)))
            pairnum, _ = self.color_pairs.get(fgbg, (None, ''))
            if pairnum is None:
                if len(self.color_pairs) > 254:
                    self.color_pairs.clear()  # start over
                    self.color_cache.clear()
                pairnum = len(self.color_pairs)+1
                try:
                    curses.init_pair(pairnum, *fgbg)
                except curses.error as e:
                    return ColorAttr(0, attrs, precedence, attrs)
                self.color_pairs[fgbg] = (pairnum, colornamestr)

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
