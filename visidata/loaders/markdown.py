from visidata import *

def markdown_escape(s, style='orgmode'):
    if style == 'jira':
        return s

    ret = ''
    for ch in s:
        if ch in '\`*_{}[]()>#+-.!':
            ret += '\\'+ch
        else:
            ret += ch
    return ret

def markdown_colhdr(col):
    if isNumeric(col):
        return ('-' * (col.width-1)) + ':'
    else:
        return '-' * (col.width or options.default_width)

def write_md(p, *vsheets, md_style='orgmode'):
    'pipe tables compatible with org-mode'

    if md_style == 'jira':
        delim = '||'
    else:
        delim = '|'

    with p.open_text(mode='w') as fp:
        for vs in vsheets:
            if len(vsheets) > 1:
                fp.write('# %s\n\n' % vs.name)

            fp.write(delim + delim.join('%-*s' % (col.width or options.default_width, markdown_escape(col.name, md_style)) for col in vs.visibleCols) + '|\n')
            if md_style == 'orgmode':
                fp.write('|' + '|'.join(markdown_colhdr(col) for col in vs.visibleCols) + '|\n')

            with Progress(gerund='saving'):
                for row in vs.itervalues():
                    s = '|'
                    for col, val in row.items():
                        s += '%-*s|' % (col.width or options.default_width, markdown_escape(val, md_style))
                    s += '\n'
                    fp.write(s)
            fp.write('\n')

    vd.status('%s save finished' % p)


def save_md(p, vsheets):
    write_md(p, vsheets, md_style='orgmode')


def save_jira(p, vsheets):
    write_md(p, vsheets, md_style='jira')


multisave_md = save_md
