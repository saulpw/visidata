import math
import functools
import collections

from visidata import Progress, isNullFunc, Column
from visidata import *


@Column.api
def getValueRows(self, rows):
    'Generate (val, row) for the given `rows` at this Column, excluding errors and nulls.'
    f = isNullFunc()

    for r in Progress(rows, 'calculating'):
        try:
            v = self.getTypedValue(r)
            if not f(v):
                yield v, r
        except Exception:
            pass

@Column.api
def getValues(self, rows):
    for v, r in self.getValueRows(rows):
        yield v


aggregators = collections.OrderedDict()  # [aggname] -> annotated func, or list of same

class Aggregator:
    def __init__(self, name, type, func, helpstr='foo'):
        'Define aggregator `name` that calls func(col, rows)'
        self.type = type
        self.func = func
        self.helpstr = helpstr
        self.name = name

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

_defaggr = Aggregator

def aggregator(name, func, helpstr='', *args, type=None):
    'Define simple aggregator `name` that calls func(values)'
    def _func(col, rows):  # wrap builtins so they can have a .type
        vals = list(col.getValues(rows))
        try:
            return func(vals, *args)
        except Exception as e:
            if len(vals) == 0:
                return None
            return e

    aggregators[name] = _defaggr(name, type, _func, helpstr)

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
def percentile(pct, helpstr=''):
    return _defaggr('p%s'%pct, None, lambda col,rows,pct=pct: _percentile(sorted(col.getValues(rows)), pct/100), helpstr)

def quantiles(q, helpstr):
    return [percentile(round(100*i/q), helpstr) for i in range(1, q)]

aggregator('min', min, 'minimum value')
aggregator('max', max, 'minimum value')
aggregator('avg', mean, 'arithmetic mean of values', type=float)
aggregator('mean', mean, 'arithmetic mean of values', type=float)
aggregator('median', median, 'median of values')
aggregator('sum', sum, 'sum of values')
aggregator('distinct', set, 'distinct values', type=vlen)
aggregator('count', lambda values: sum(1 for v in values), 'number of values', type=int)
aggregator('list', list, 'list of values')

aggregators['q3'] = quantiles(3, 'tertiles (33/66th pctile)')
aggregators['q4'] = quantiles(4, 'quartiles (25/50/75th pctile)')
aggregators['q5'] = quantiles(5, 'quintiles (20/40/60/80th pctiles)')
aggregators['q10'] = quantiles(10, 'deciles (10/20/30/40/50/60/70/80/80th pctiles)')

# returns keys of the row with the max value
aggregators['keymax'] = _defaggr('keymax', anytype, lambda col, rows: col.sheet.rowkey(max(col.getValueRows(rows))[1]), 'key of the maximum value')


ColumnsSheet.columns += [
        Column('aggregators',
               getter=lambda col,row: ' '.join(x.name for x in getattr(row, 'aggregators', [])),
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
                if aggr and aggr not in c.aggregators:
                    c.aggregators += [aggr]


@Column.api
def aggname(col, agg):
    'Consistent formatting of the name of given aggregator for this column.  e.g. "col1_sum"'
    return '%s_%s' % (col.name, agg.name)

@Column.api
@asyncthread
def show_aggregate(col, agg, rows):
    'Show aggregated value in status, and add to memory.'
    aggval = agg(col, rows)
    typedval = wrapply(agg.type or col.type, aggval)
    dispval = col.format(typedval)
    vd.status(dispval)


aggregator_choices = [
    {'key': agg, 'desc': v[0].helpstr if isinstance(v, list) else v.helpstr} for agg, v in aggregators.items()
]

addGlobals(globals())


Sheet.addCommand('+', 'aggregate-col', 'addAggregators([cursorCol], chooseMany(aggregator_choices))', 'add aggregator to current column')
Sheet.addCommand('z+', 'show-aggregate', 'for agg in chooseMany(aggregators_choices): cursorCol.show_aggregate(agg["key"],  selectedRows or rows)', 'display result of aggregator over values in selected rows for current column')
ColumnsSheet.addCommand('g+', 'aggregate-cols', 'addAggregators(selectedRows or source[0].nonKeyVisibleCols, chooseMany(aggregator_choices))', 'add aggregators to selected source columns')
