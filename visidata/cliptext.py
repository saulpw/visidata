import unicodedata
import sys
import re
import functools
import textwrap

from visidata import options, drawcache, vd, update_attr, colors, ColorAttr

disp_column_fill = ' '
internal_markup_re = r'(\[[:/][^\]]*?\])'  # [:whatever until the closing bracket] or [/whatever] or [:]

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


def is_vdcode(s:str) -> bool:
    return (s.startswith('[:') and s.endswith(']')) or \
           (s.startswith('[/') and s.endswith(']'))


def iterchunks(s, literal=False):
    attrstack = [dict(link='', cattr=ColorAttr())]
    legitopens = 0
    chunks = re.split(internal_markup_re, s)
    for chunk in chunks:
        if not chunk:
            continue

        if not literal and is_vdcode(chunk):
            cattr = attrstack[-1]['cattr']
            link = attrstack[-1]['link']

            if chunk.startswith('[:onclick '):
                attrstack.append(dict(link=chunk[2:-1], cattr=cattr.update(colors.clickable)))
                continue
            elif chunk == '[:]':  # clear stack, keep origattr
                if len(attrstack) > 1:
                    del attrstack[1:]
                    continue
            elif chunk.startswith('[/'):  # pop last attr off stack
                if len(attrstack) > 1:
                    attrstack.pop()
                continue  # don't display trailing [/foo] ever
            else:  # push updated color on stack
                newcolor = colors.get_color(chunk[2:-1])
                if newcolor:
                    cattr = update_attr(cattr, newcolor, len(attrstack))
                    attrstack.append(dict(link=link, cattr=cattr))
                    continue

        yield attrstack[-1], chunk


@functools.lru_cache(maxsize=100000)
def dispwidth(ss, maxwidth=None, literal=False):
    'Return display width of string, according to unicodedata width and options.disp_ambig_width.'
    disp_ambig_width = options.disp_ambig_width
    w = 0

    for _, s in iterchunks(ss, literal=literal):
        for cc in s:
            if cc:
                w += wcwidth(cc, disp_ambig_width)
                if maxwidth and w > maxwidth:
                    return maxwidth
    return w


@functools.lru_cache(maxsize=100000)
def _dispch(c, oddspacech=None, combch=None, modch=None):
    ccat = unicodedata.category(c)
    if ccat in ['Mn', 'Sk', 'Lm']:
        if unicodedata.name(c).startswith('MODIFIER'):
            return modch, 1
    elif c != ' ' and ccat in ('Cc', 'Zs', 'Zl', 'Cs'):  # control char, space, line sep, surrogate
        return oddspacech, 1
    elif c in ZERO_WIDTH_CF:
        return combch, 1

    return c, dispwidth(c, literal=True)


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
    ''' *s* is a string or an iterator that contains characters.
    *dispw* is the integer screen width that the clipped string will fit inside, or None.
    Return clipped string and width in terminal display characters.
    Note: width may differ from len(s) if chars are 'fullwidth'.
    If *dispw* is None, no clipping occurs.
    If *trunch* has a width greater than *dispw*, the empty string
    will be used as a truncator instead.'''
    if not s or (dispw is not None and dispw < 1): #iterator s would be truthy
        return '', 0

    w = 0
    ret = ''
    trunc_i = 0
    w_truncated = 0

    trunchlen = dispwidth(trunch)
    if dispw is None:
        s = ''.join(s)
        return s, dispwidth(s)
    if trunchlen > dispw: #if the truncator cannot fit, use a truncator of ''
        return _clipstr(s, dispw, trunch='', oddspacech=oddspacech, combch=combch, modch=modch)
    for c in s:
        newc, chlen = _dispch(c, oddspacech=oddspacech, combch=combch, modch=modch)
        if not newc:
            newc = c
            chlen = dispwidth(c)

        #if the next character will fit
        if w+chlen <= dispw:
            ret += c
            w += chlen
            #move the truncation spot forward only when the truncation character can fit
            if w+trunchlen <= dispw:
                trunc_i += 1
                w_truncated += chlen
            continue
        # if we reach this line, a character did not fit, and the result needs truncation
        return ret[:trunc_i] + trunch, w_truncated+trunchlen

    return ret, w


@drawcache
def clipstr(s, dispw, truncator=None, oddspace=None):
    ''' *s* is a string or an iterator that contains characters.
    *dispw* is the integer screen width that the clipped string will fit inside, or None.'''
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


def clipdraw(scr, y, x, s, attr, w=None, clear=True, literal=False, **kwargs):
    '''Draw `s`  at (y,x)-(y,x+w) with curses `attr`, clipping with ellipsis char.
       If `clear`, clear whole editing area before displaying.
       If `literal`, do not interpret internal color code markup.
       Return width drawn (max of w).
    '''
    if not literal:
        chunks = iterchunks(s, literal=literal)
    else:
        chunks = [(dict(link='', cattr=ColorAttr()), s)]

    x = max(0, x)
    y = max(0, y)

    return clipdraw_chunks(scr, y, x, chunks, attr, w=w, clear=clear, **kwargs)


def clipdraw_chunks(scr, y, x, chunks, cattr:ColorAttr=ColorAttr(), w=None, clear=True, literal=False, **kwargs):
    '''Draw `chunks` (sequence of (color:str, text:str) as from iterchunks) at (y,x)-(y,x+w) with curses `attr`, clipping with ellipsis char.
       If `clear`, clear whole editing area before displaying.
       Return width drawn (max of w).
    '''
    if scr:
        windowHeight, windowWidth = scr.getmaxyx()
    else:
        windowHeight, windowWidth = 25, 80
    totaldispw = 0

    assert isinstance(cattr, ColorAttr), cattr
    origattr = cattr
    origw = w
    clipped = ''
    link = ''

    if w and clear:
        actualw = min(w, windowWidth-x-1)
        if scr:
            scr.addstr(y, x, disp_column_fill*actualw, cattr.attr)  # clear whole area before displaying

    try:
        for colorstate, chunk in chunks:
            if colorstate:
                if isinstance(colorstate, str):
                    cattr = cattr.update(colors.get_color(colorstate), 100)
                else:
                    cattr = origattr.update(colorstate['cattr'], 100)
                    link = colorstate['link']

            if not chunk:
                continue

            if origw is None:
                chunkw = dispwidth(chunk, maxwidth=windowWidth-totaldispw)
            else:
                chunkw = origw-totaldispw

            chunkw = min(chunkw, windowWidth-x-1)
            if chunkw <= 0:  # no room anyway
                return totaldispw
            if not scr:
                return totaldispw

            # convert to string just before drawing
            clipped, dispw = clipstr(chunk, chunkw, **kwargs)

            if y >= 0 and y < windowHeight:
                scr.addstr(y, x, clipped, cattr.attr)
            else:
                if vd.options.debug:
                    raise Exception(f'addstr(y={y} x={x}) out of bounds')

            if link:
                vd.onMouse(scr, x, y, dispw, 1, BUTTON1_RELEASED=link)

            x += dispw
            totaldispw += dispw

            if chunkw < dispw:
                break
    except Exception as e:
        if vd.options.debug:
            raise
#        raise type(e)('%s [clip_draw y=%s x=%s dispw=%s w=%s clippedlen=%s]' % (e, y, x, totaldispw, w, len(clipped))
#                ).with_traceback(sys.exc_info()[2])

    return totaldispw


def _markdown_to_internal(text):
    'Return markdown-formatted `text` converted to internal formatting (like `[:color]text[/]`).'
    text = re.sub(r'`(.*?)`', r'[:code]\1[/]', text)
    text = re.sub(r'(^#.*?)$', r'[:heading]\1[/]', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'[:bold]\1[/]', text)
    text = re.sub(r'\*(.*?)\*', r'[:italic]\1[/]', text)
    text = re.sub(r'\b_(.*?)_\b', r'[:underline]\1[/]', text)
    return text


def wraptext(text, width=80, indent=''):
    '''
    Word-wrap `text` and yield (formatted_line, textonly_line) for each line of at most `width` characters.
    Formatting like `[:color]text[/]` is ignored for purposes of computing width, and not included in `textonly_line`.
    '''
    import re

    if width <= 0:
        return

    for line in text.splitlines():
        if not line:
            yield '', ''
            continue

        line = _markdown_to_internal(line)
        chunks = re.split(internal_markup_re, line)
        textchunks = [x for x in chunks if not is_vdcode(x)]
        # textwrap.wrap does not handle variable-width characters  #2416
        for linenum, textline in enumerate(textwrap.wrap(''.join(textchunks), width=width, drop_whitespace=False)):
            txt = textline
            r = ''
            while chunks:
                c = chunks[0]
                if len(c) > len(txt):
                    r += txt
                    chunks[0] = c[len(txt):]
                    break

                if len(chunks) == 1:
                    r += chunks.pop(0)
                else:
                    chunks.pop(0)
                    r += txt[:len(c)] + chunks.pop(0)

                txt = txt[len(c):]

            r = r.strip()
            if linenum > 0:
                r = indent + r
            yield r, textline

        for c in chunks:
            yield c, ''


def clipbox(scr, lines, attr, title=''):
    scr.erase()
    scr.bkgd(attr)
    scr.box()
    h, w = scr.getmaxyx()
    for i, line in enumerate(lines):
        clipdraw(scr, i+1, 2, line, attr)

    clipdraw(scr, 0, w-dispwidth(title)-6, f"| {title} |", attr)

def clipstr_start(dispval, w, truncator=''):
    '''Return a tuple (frag, dw), where *frag* is the longest ending substring
    of *dispval* that will fit in a space *w* terminal display characters wide,
    and *dw* is the substring's display width as an int.'''
    # Note: this implementation is likely incorrect for unusual Unicode
    # strings or encodings, where trimming an initial character produces
    # an invalid string or does not make the string shorter.
    if w <= 0: return '', 0
    j = len(dispval)
    while j >= 1:
        if dispwidth((truncator if j > 1 else '') + dispval[j-1:]) <= w:
            j -= 1
        else:
            break
    frag = (truncator if j > 0 else '') + dispval[j:]
    return frag, dispwidth(frag)

def clipstr_middle(s, n=10, truncator='…'):
    '''Return a string having a display width <= *n*. Excess characters are
    trimmed from the middle of the string, and replaced by a single
    instance of *truncator*.'''
    if n == 0: return '', 0
    if dispwidth(s) > n:
        #for even widths, give the leftover 1 space to the right fragment
        l_space = n//2 if n%2 == 1 else max(n//2-1, 0)
        l_frag, l_w = _clipstr(s, l_space)
        #if left fragment did not fill its space, give the unused space to the right fragment
        r_frag = clipstr_start(s, n//2+(l_space-l_w))[0]
        res = l_frag + truncator + r_frag
        return res, dispwidth(res)
    return s, dispwidth(s)

vd.addGlobals(clipstr=clipstr,
              clipdraw=clipdraw,
              clipdraw_chunks=clipdraw_chunks,
              clipbox=clipbox,
              dispwidth=dispwidth,
              iterchars=iterchars,
              iterchunks=iterchunks,
              wraptext=wraptext,
              clipstr_start=clipstr_start,
              clipstr_middle=clipstr_middle)
