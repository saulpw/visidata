import math
import functools
import collections

from visidata import *

Sheet.addCommand('+', 'aggregate-col', 'addAggregators([cursorCol], chooseMany(aggregators.keys()))')
Sheet.addCommand('z+', 'show-aggregate', 'agg=chooseOne(aggregators); status(cursorCol.format(wrapply(agg.type or cursorCol.type, agg(cursorCol, rows))))')

aggregators = collections.OrderedDict()

def _defaggr(name, type, func):
    'Define aggregator `name` that calls func(col, rows)'
    func.type=type
    func.__name__ = name
    return func

def aggregator(name, func, *args, type=None):
    'Define simple aggregator `name` that calls func(values)'
    def _func(col, rows):  # wrap builtins so they can have a .type
        return func(col.getValues(rows), *args)
    aggregators[name] = _defaggr(name, type, _func)

## specific aggregator implementations

def mean(vals):
    vals = list(vals)
    if vals:
        return float(sum(vals))/len(vals)

def median(values):
    L = sorted(values)
    return L[len(L)//2]

# http://code.activestate.com/recipes/511478-finding-the-percentile-of-the-values/
def _percentile(N, percent, key=lambda x:x):
    """
    Find the percentile of a list of values.

    @parameter N - is a list of values. Note N MUST BE already sorted.
    @parameter percent - a float value from 0.0 to 1.0.
    @parameter key - optional key function to compute value from each element of N.

    @return - the percentile of the values
    """
    if not N:
        return None
    k = (len(N)-1) * percent
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return key(N[int(k)])
    d0 = key(N[int(f)]) * (c-k)
    d1 = key(N[int(c)]) * (k-f)
    return d0+d1

@functools.lru_cache(100)
def percentile(pct):
    return _defaggr('p%s'%pct, None, lambda col,rows,pct=pct: _percentile(sorted(col.getValues(rows)), pct/100))

def quantiles(q):
    return [percentile(round(100*i/q)) for i in range(1, q)]

aggregator('min', min)
aggregator('max', max)
aggregator('avg', mean, type=float)
aggregator('mean', mean, type=float)
aggregator('median', median)
aggregator('sum', sum)
aggregator('distinct', set, type=len)
aggregator('count', lambda values: sum(1 for v in values), type=int)

aggregators['q3'] = quantiles(3)
aggregators['q4'] = quantiles(4)
aggregators['q5'] = quantiles(5)
aggregators['q10'] = quantiles(10)

# returns keys of the row with the max value
aggregators['keymax'] = _defaggr('keymax', anytype, lambda col, rows: col.sheet.rowkey(max(col.getValueRows(rows))[1]))

ColumnsSheet.addCommand('g+', 'aggregate-cols', 'addAggregators(selectedRows or source[0].nonKeyVisibleCols, chooseMany(aggregators.keys()))')

ColumnsSheet.columns += [
        Column('aggregators',
               getter=lambda col,row: ' '.join(x.__name__ for x in getattr(row, 'aggregators', [])),
               setter=lambda col,row,val: setattr(row, 'aggregators', list(aggregators[k] for k in (val or '').split())))
]

def addAggregators(cols, aggrnames):
    'add aggregator for each aggrname to each of cols'
    for aggrname in aggrnames:
        aggrs = aggregators.get(aggrname)
        aggrs = aggrs if isinstance(aggrs, list) else [aggrs]
        for aggr in aggrs:
            for c in cols:
                if not hasattr(c, 'aggregators'):
                    c.aggregators = []
                if aggr not in c.aggregators:
                    c.aggregators += [aggr]


addGlobals(globals())
