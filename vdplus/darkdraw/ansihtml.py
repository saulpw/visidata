from unittest import mock
from visidata import AttrDict, VisiData, colors

from .drawing import Drawing, DrawingSheet


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


def htmlattrstr(r, attrnames, **kwargs):
    d = AttrDict(kwargs)
    for a in attrnames:
        if a in r:
            d[a] = r[a]
    return ' '.join('%s="%s"' % (k,v) for k, v in d.items())


@VisiData.api
def save_ansihtml(vd, p, *sheets):
    for vs in sheets:
        if isinstance(vs, DrawingSheet):
            dwg = Drawing('', source=vs)
        elif isinstance(vs, Drawing):
            dwg = vs
        else:
            vd.fail(f'{vs.name} not a drawing')

        dwg._scr = mock.MagicMock(__bool__=mock.Mock(return_value=True),
                                  getmaxyx=mock.Mock(return_value=(9999, 9999)))
        dwg.draw(dwg._scr)
        body = '''<pre>'''
        for y in range(dwg.minY, dwg.maxY+1):
            for x in range(dwg.minX, dwg.maxX+1):
                rows = dwg._displayedRows.get((x,y), None)
                if not rows:
                    body += ' '
                else:
                    r = rows[-1]
                    ch = r.text[x-r.x]
                    fg, bg, attrs = colors.split_colorstr(r.color)

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

                    spanattrstr = htmlattrstr(r, 'id class'.split(), style=style)
                    span = f'<span {spanattrstr}>{ch}</span>'
                    if r.href:
                        linkattrstr = htmlattrstr(r, 'href title'.split())
                        body += f'<a {linkattrstr}>{span}</a>'
                    else:
                        body += span

            body += '\n'
        body += '</pre>\n'

    try:
        tmpl = open('ansi.html').read()
        out = tmpl.replace('<body>', '<body>'+body)
    except FileNotFoundError:
        out = body

    with p.open_text(mode='w') as fp:
        fp.write(out)
