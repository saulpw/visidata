from visidata import *

def markdown_escape(s):
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

@async
def save_md(vs, fn):
    'pipe tables compatible with org-mode'

    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        fp.write('|' + '|'.join('%-*s' % (col.width or options.default_width, markdown_escape(col.name)) for col in vs.visibleCols) + '|\n')
        fp.write('|' + '+'.join(markdown_colhdr(col) for col in vs.visibleCols) + '|\n')

        for row in Progress(vs.rows):
            fp.write('|' + '|'.join('%-*s' % (col.width or options.default_width, markdown_escape(col.getDisplayValue(row))) for col in vs.visibleCols) + '|\n')

    status('%s save finished' % fn)

