import math
import functools
import collections
from statistics import mode, stdev

from visidata import Progress, Column
from visidata import *


@Column.api
def getValueRows(self, rows):
    'Generate (value, row) for each row in *rows* at this column, excluding null and error values.'
    f = self.sheet.isNullFunc()

    for r in Progress(rows, 'calculating'):
        try:
            v = self.getTypedValue(r)
            if not f(v):
                yield v, r
        except Exception:
            pass

@Column.api
def getValues(self, rows):
    'Generate value for each row in *rows* at this column, excluding null and error values.'
    for v, r in self.getValueRows(rows):
        yield v


vd.aggregators = collections.OrderedDict()  # [aggname] -> annotated func, or list of same

Column.init('aggstr', str, copy=True)

def aggregators_get(col):
    'A space-separated names of aggregators on this column.'
    return list(vd.aggregators[k] for k in (col.aggstr or '').split())

def aggregators_set(col, aggs):
    if isinstance(aggs, str):
        newaggs = []
        for agg in aggs.split():
            if agg not in vd.aggregators:
                vd.fail(f'unknown aggregator {agg}')
            newaggs.append(agg)
    elif aggs is None:
        newaggs = ''
    else:
        newaggs = [agg.name for agg in aggs]

    col.aggstr = ' '.join(newaggs)

Column.aggregators = property(aggregators_get, aggregators_set)


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

@VisiData.api
def aggregator(vd, name, func, helpstr='', *args, type=None):
    'Define simple aggregator *name* that calls ``func(values, *args)`` to aggregate *values*.  Use *type* to force the default type of the aggregated column.'
    def _func(col, rows):  # wrap builtins so they can have a .type
        vals = list(col.getValues(rows))
        try:
            return func(vals, *args)
        except Exception as e:
            if len(vals) == 0:
                return None
            return e

    vd.aggregators[name] = _defaggr(name, type, _func, helpstr)
    vd.addGlobals({name: func})

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

vd.aggregator('min', min, 'minimum value')
vd.aggregator('max', max, 'maximum value')
vd.aggregator('avg', mean, 'arithmetic mean of values', type=float)
vd.aggregator('mean', mean, 'arithmetic mean of values', type=float)
vd.aggregator('median', median, 'median of values')
vd.aggregator('mode', mode, 'mode of values')
vd.aggregator('sum', sum, 'sum of values')
vd.aggregator('distinct', set, 'distinct values', type=vlen)
vd.aggregator('count', lambda values: sum(1 for v in values), 'number of values', type=int)
vd.aggregator('list', list, 'list of values')
vd.aggregator('stdev', stdev, 'standard deviation of values', type=float)

vd.aggregators['q3'] = quantiles(3, 'tertiles (33/66th pctile)')
vd.aggregators['q4'] = quantiles(4, 'quartiles (25/50/75th pctile)')
vd.aggregators['q5'] = quantiles(5, 'quintiles (20/40/60/80th pctiles)')
vd.aggregators['q10'] = quantiles(10, 'deciles (10/20/30/40/50/60/70/80/90th pctiles)')

# since bb29b6e, a record of every aggregator
# is needed in vd.aggregators
for pct in (10, 20, 25, 30, 33, 40, 50, 60, 67, 70, 75, 80, 90):
    vd.aggregators[f'p{pct}'] = percentile(pct, f'{pct}th percentile')

# returns keys of the row with the max value
vd.aggregators['keymax'] = _defaggr('keymax', anytype, lambda col, rows: col.sheet.rowkey(max(col.getValueRows(rows))[1]), 'key of the maximum value')


ColumnsSheet.columns += [
    Column('aggregators',
           getter=lambda c,r:r.aggstr,
           setter=lambda c,r,v:setattr(r, 'aggregators', v))
]

@Sheet.api
def addAggregators(sheet, cols, aggrnames):
    'Add each aggregator in list of *aggrnames* to each of *cols*.'
    for aggrname in aggrnames:
        aggrs = vd.aggregators.get(aggrname)
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
def memo_aggregate(col, agg, rows):
    'Show aggregated value in status, and add to memory.'
    aggval = agg(col, rows)
    typedval = wrapply(agg.type or col.type, aggval)
    dispval = col.format(typedval)
    k = col.name+'_'+agg.name
    vd.status(f'{k}={dispval}')
    vd.memory[k] = typedval


@VisiData.property
def aggregator_choices(vd):
    return [
       {'key': agg, 'desc': v[0].helpstr if isinstance(v, list) else v.helpstr} for agg, v in vd.aggregators.items()
    ]


Sheet.addCommand('+', 'aggregate-col', 'addAggregators([cursorCol], chooseMany(aggregator_choices))', 'Add aggregator to current column')
Sheet.addCommand('z+', 'memo-aggregate', 'for agg in chooseMany(aggregator_choices): cursorCol.memo_aggregate(aggregators[agg], selectedRows or rows)', 'memo result of aggregator over values in selected rows for current column')
ColumnsSheet.addCommand('g+', 'aggregate-cols', 'addAggregators(selectedRows or source[0].nonKeyVisibleCols, chooseMany(aggregator_choices))', 'add aggregators to selected source columns')
