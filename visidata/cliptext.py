import unicodedata
import sys
import functools

from visidata import options

__all__ = ['clipstr', 'clipdraw', 'dispwidth']

disp_column_fill = ' '

### Curses helpers

def dispwidth(ss):
    'Return display width of string, according to unicodedata width and options.disp_ambig_width.'
    disp_ambig_width = options.disp_ambig_width
    w = 0

    for cc in ss:
        eaw = unicodedata.east_asian_width(cc)
        if eaw == 'A':  # ambiguous
            w += disp_ambig_width
        elif eaw in 'WF': # wide/full
            w += 2
        elif not unicodedata.combining(cc):
            w += 1
    return w


@functools.lru_cache(maxsize=100000)
def clipstr(s, dispw):
    '''Return clipped string and width in terminal display characters.
    Note: width may differ from len(s) if East Asian chars are 'fullwidth'.'''
    w = 0
    ret = ''
    trunch = options.disp_truncator
    for c in s:
        if c != ' ' and unicodedata.category(c) in ('Cc', 'Zs', 'Zl'):  # control char, space, line sep
            c = options.disp_oddspace

        if c:
            c = c[0]  # multi-char disp_oddspace just uses the first char
            ret += c
            w += dispwidth(c)

        if w > dispw-len(trunch)+1:
            ret = ret[:-2] + trunch # replace final char with ellipsis
            w += len(trunch)
            break

    return ret, w


def clipdraw(scr, y, x, s, attr, w=None, rtl=False):
    'Draw string `s` at (y,x)-(y,x+w) with curses attr, clipping with ellipsis char.  if rtl, draw inside (x-w, x).  Returns width drawn (max of w).'
    if not scr:
        return 0
    _, windowWidth = scr.getmaxyx()
    dispw = 0
    try:
        if w is None:
            w = len(s)
        w = min(w, (x-1) if rtl else (windowWidth-x-1))
        if w <= 0:  # no room anyway
            return 0

        # convert to string just before drawing
        clipped, dispw = clipstr(str(s), w)
        if rtl:
            # clearing whole area (w) has negative display effects; clearing just dispw area is useless
#            scr.addstr(y, x-dispw-1, disp_column_fill*dispw, attr)
            scr.addstr(y, x-dispw-1, clipped, attr)
        else:
            scr.addstr(y, x, disp_column_fill*w, attr)  # clear whole area before displaying
            scr.addstr(y, x, clipped, attr)
    except Exception as e:
        pass
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s clippedlen=%s]' % (e, y, x, dispw, w, len(clipped))
#                ).with_traceback(sys.exc_info()[2])

    return dispw
