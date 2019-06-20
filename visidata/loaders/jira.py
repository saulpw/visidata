from visidata import *

def save_jira(p, *vsheets):
    'jira style table markdown (confluence wiki)'
    with p.open_text(mode='w') as fp:
        for vs in vsheets:
            if len(vsheets) > 1:
                fp.write('# %s\n\n' % vs.name)
            fp.write('||' + '||'.join('%-*s' % ((col.width or options.default_width) - 1, col.name) for col in vs.visibleCols) + '||\n')

            for row in Progress(vs.rows, 'saving'):
                fp.write('|' + '|'.join('%-*s' % (col.width or options.default_width, col.getDisplayValue(row)) for col in vs.visibleCols) + '|\n')
            fp.write('\n')

    status('%s save finished' % p)

multisave_jira = save_jira
