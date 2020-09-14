"""
Generate sparkline column for numeric columns
"""
from visidata import Column, Sheet, option, options

__author__ = 'Lucas Messenger @layertwo'
__version__ = '0.2'


option('disp_sparkline', '▁▂▃▄▅▆▇', 'characters to display sparkline')


def sparkline(*values):
    """
    From *values generate string sparkline
    """
    lines = options.disp_sparkline
    values = [v for v in values if isinstance(v, (int, float))]
    mx = max(values)
    mn = min(values)
    w = (mx - mn) / len(lines)
    bounds = [(mn + w * i) for i in range(len(lines))]

    output = ''
    for val in values:
        for b in bounds:
            if mn == 0 and val == 0:
                output += ' '
                break
            if val < b:
                output += lines[bounds.index(b) - 1]
                break
        else:
            output += max(lines)
    return output


@Sheet.api
def sparkline_col(sheet, source):
    """
    Add sparkline column
    """
    c = Column('sparkline',
               getter=lambda c,r: sparkline(*tuple(c.getTypedValue(r) for c in source)))
    sheet.addColumn(c)


Sheet.addCommand(None, 'addcol-sparkline', 'sheet.sparkline_col(numericCols(nonKeyVisibleCols))')
