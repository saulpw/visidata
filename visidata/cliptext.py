import unicodedata
import sys
import functools

from visidata import options, drawcache

__all__ = ['clipstr', 'clipdraw', 'clipbox', 'dispwidth', 'iterchars']

disp_column_fill = ' '

### Curses helpers

# ZERO_WIDTH_CF is from wcwidth:
# NOTE: created by hand, there isn't anything identifiable other than
# general Cf category code to identify these, and some characters in Cf
# category code are of non-zero width.
# Also includes some Cc, Mn, Zl, and Zp characters
ZERO_WIDTH_CF = set(map(chr, [
    0,       # Null (Cc)
    0x034F,  # Combining grapheme joiner (Mn)
    0x200B,  # Zero width space
    0x200C,  # Zero width non-joiner
    0x200D,  # Zero width joiner
    0x200E,  # Left-to-right mark
    0x200F,  # Right-to-left mark
    0x2028,  # Line separator (Zl)
    0x2029,  # Paragraph separator (Zp)
    0x202A,  # Left-to-right embedding
    0x202B,  # Right-to-left embedding
    0x202C,  # Pop directional formatting
    0x202D,  # Left-to-right override
    0x202E,  # Right-to-left override
    0x2060,  # Word joiner
    0x2061,  # Function application
    0x2062,  # Invisible times
    0x2063,  # Invisible separator
]))

def wcwidth(cc, ambig=1):
        if cc in ZERO_WIDTH_CF:
            return 1
        eaw = unicodedata.east_asian_width(cc)
        if eaw in 'AN':  # ambiguous or neutral
            if unicodedata.category(cc) == 'Mn':
                return 1
            else:
                return ambig
        elif eaw in 'WF': # wide/full
            return 2
        elif not unicodedata.combining(cc):
            return 1
        return 0


@functools.lru_cache(maxsize=100000)
def dispwidth(ss, maxwidth=None):
    'Return display width of string, according to unicodedata width and options.disp_ambig_width.'
    disp_ambig_width = options.disp_ambig_width
    w = 0

    for cc in ss:
        w += wcwidth(cc, disp_ambig_width)
        if maxwidth and w > maxwidth:
            break
    return w


@functools.lru_cache(maxsize=100000)
def _dispch(c, oddspacech=None, combch=None, modch=None):
    ccat = unicodedata.category(c)
    if ccat in ['Mn', 'Sk', 'Lm']:
        if unicodedata.name(c).startswith('MODIFIER'):
            return modch, 1
    elif c != ' ' and ccat in ('Cc', 'Zs', 'Zl'):  # control char, space, line sep
        return oddspacech, 1
    elif c in ZERO_WIDTH_CF:
        return combch, 1

    return c, dispwidth(c)


def iterchars(x):
    if isinstance(x, dict):
        yield from '{%d}' % len(x)
        for k, v in x.items():
            yield ' '
            yield from iterchars(k)
            yield '='
            yield from iterchars(v)

    elif isinstance(x, (list, tuple)):
        yield from '[%d] ' % len(x)
        for i, v in enumerate(x):
            if i != 0:
                yield from '; '
            yield from iterchars(v)

    else:
        yield from str(x)


@functools.lru_cache(maxsize=100000)
def _clipstr(s, dispw, trunch='', oddspacech='', combch='', modch=''):
    '''Return clipped string and width in terminal display characters.
    Note: width may differ from len(s) if East Asian chars are 'fullwidth'.'''
    w = 0
    ret = ''

    trunchlen = dispwidth(trunch)
    for c in s:
        newc, chlen = _dispch(c, oddspacech=oddspacech, combch=combch, modch=modch)
        if newc:
            ret += newc
            w += chlen
        else:
            ret += c
            w += dispwidth(c)

        if dispw and w > dispw-trunchlen+1:
            ret = ret[:-2] + trunch # replace final char with ellipsis
            w += trunchlen
            break

    return ret, w


@drawcache
def clipstr(s, dispw, truncator=None, oddspace=None):
    if options.visibility:
        return _clipstr(s, dispw,
                        trunch=options.disp_truncator if truncator is None else truncator,
                        oddspacech=options.disp_oddspace if oddspace is None else oddspace,
                        modch='\u25e6',
                        combch='\u25cc')
    else:
        return _clipstr(s, dispw,
                trunch=options.disp_truncator if truncator is None else truncator,
                oddspacech=options.disp_oddspace if oddspace is None else oddspace,
                modch='',
                combch='')

def clipdraw(scr, y, x, s, attr, w=None, clear=True, rtl=False, **kwargs):
    'Draw string `s` at (y,x)-(y,x+w) with curses attr, clipping with ellipsis char.  if rtl, draw inside (x-w, x).  If *clear*, clear whole editing area before displaying. Returns width drawn (max of w).'
    if scr:
        _, windowWidth = scr.getmaxyx()
    else:
        windowWidth = 80
    dispw = 0
    try:
        if w is None:
            w = dispwidth(s, maxwidth=windowWidth)
        w = min(w, (x-1) if rtl else (windowWidth-x-1))
        if w <= 0:  # no room anyway
            return 0
        if not scr:
            return w

        # convert to string just before drawing
        clipped, dispw = clipstr(s, w, **kwargs)
        if rtl:
            # clearing whole area (w) has negative display effects; clearing just dispw area is useless
#            scr.addstr(y, x-dispw-1, disp_column_fill*dispw, attr)
            scr.addstr(y, x-dispw-1, clipped, attr)
        else:
            if clear:
                scr.addstr(y, x, disp_column_fill*w, attr)  # clear whole area before displaying
            scr.addstr(y, x, clipped, attr)
    except Exception as e:
        pass
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s clippedlen=%s]' % (e, y, x, dispw, w, len(clipped))
#                ).with_traceback(sys.exc_info()[2])

    return dispw


def clipbox(scr, lines, attr, title=''):
    scr.erase()
    scr.bkgd(attr)
    scr.box()
    h, w = scr.getmaxyx()
    clipdraw(scr, 0, w-len(title)-6, f"| {title} |", attr)
    for i, line in enumerate(lines):
        clipdraw(scr, i+1, 2, line, attr)
