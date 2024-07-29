from visidata import VisiData, vd, options, Progress

def markdown_link(s, href):
    if not href:
        return s

    return f'[{s}]({href})'

def markdown_escape(s, style='orgmode'):
    if style == 'jira':
        return s

    ret = ''
    for ch in s:
        if ch in '\\`*_{}[]()>#+-.!':
            ret += '\\'+ch
        else:
            ret += ch
    return ret

def markdown_colhdr(col):
    if vd.isNumeric(col):
        return ('-' * (col.width-1)) + ':'
    else:
        return '-' * (col.width or options.default_width)

def write_md(p, *vsheets, md_style='orgmode'):
    'pipe tables compatible with org-mode'

    if md_style == 'jira':
        delim = '||'
    else:
        delim = '|'

    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
        for vs in vsheets:
            if len(vsheets) > 1:
                fp.write('# %s\n\n' % vs.name)

            hdrs = []
            for col in vs.visibleCols:
                if col.name.endswith('_href'):
                    continue
                hdrs.append('%-*s' % (col.width or options.default_width, markdown_escape(col.name, md_style)))

            fp.write(delim + delim.join(hdrs) + delim + '\n')

            if md_style == 'orgmode':
                fp.write('|' + '|'.join(markdown_colhdr(col) for col in vs.visibleCols if not col.name.endswith('_href')) + '|\n')

            with Progress(gerund='saving'):
                for dispvals in vs.iterdispvals(format=True):
                    vals = []
                    for col, val in dispvals.items():
                        if col.name.endswith('_href'):
                            continue
                        val = markdown_escape(val, md_style)
                        linkcol = vs.colsByName.get(col.name + '_href')
                        if linkcol:
                            val = markdown_link(val, dispvals.get(linkcol))
                        vals.append('%-*s' % (col.width or options.default_width, val))
                    fp.write('|' + '|'.join(vals) + '|\n')

            fp.write('\n')


@VisiData.api
def save_md(vd, p, *sheets):
    write_md(p, *sheets, md_style='orgmode')


@VisiData.api
def save_jira(vd, p, *sheets):
    write_md(p, *sheets, md_style='jira')
