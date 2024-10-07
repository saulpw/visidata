import sys
import math
import functools
import collections
import statistics

from visidata import Progress, Sheet, Column, ColumnsSheet, VisiData
from visidata import vd, anytype, vlen, asyncthread, wrapply, AttrDict, date, INPROGRESS

vd.help_aggregators = '''# Choose Aggregators
Start typing an aggregator name or description.
Multiple aggregators can be added by separating spaces.

- `Enter` to select top aggregator.
- `Tab` to highlight top aggregator.

## When Aggregator Highlighted

- `Tab`/`Shift+Tab` to cycle highlighted aggregator.
- `Enter` to select aggregators.
- `Space` to add highlighted aggregator.
- `0-9` to add numbered aggregator.
'''

vd.option('null_value', None, 'a value to be counted as null', replay=True)


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
Column.init('_aggregatedTotals', dict)  # [aggname] -> agg total over all rows

def aggregators_get(col):
    'A space-separated names of aggregators on this column.'
    aggs = []
    for k in (col.aggstr or '').split():
        agg = vd.aggregators[k]
        aggs += agg if isinstance(agg, list) else [agg]
    return aggs

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
    def __init__(self, name, type, funcValues=None, helpstr='foo'):
        'Define aggregator `name` that calls funcValues(values)'
        self.type = type
        self.funcValues = funcValues  # funcValues(values)
        self.helpstr = helpstr
        self.name = name

    def aggregate(self, col, rows):  # wrap builtins so they can have a .type
        vals = list(col.getValues(rows))
        try:
            return self.funcValues(vals)
        except Exception as e:
            if len(vals) == 0:
                return None
            raise e


@VisiData.api
def aggregator(vd, name, funcValues, helpstr='', *, type=None):
    '''Define simple aggregator *name* that calls ``funcValues(values)`` to aggregate *values*.
       Use *type* to force type of aggregated column (default to use type of source column).'''
    vd.aggregators[name] = Aggregator(name, type, funcValues=funcValues, helpstr=helpstr)

## specific aggregator implementations

def mean(vals):
    vals = list(vals)
    if vals:
        return float(sum(vals))/len(vals)

def vsum(vals):
    return sum(vals, start=type(vals[0] if len(vals) else 0)())  #1996

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
class PercentileAggregator(Aggregator):
    def __init__(self, pct, helpstr=''):
        super().__init__('p%s'%pct, None, helpstr=helpstr)
        self.pct = pct

    def aggregate(self, col, rows):
        return _percentile(sorted(col.getValues(rows)), self.pct/100, key=float)


def quantiles(q, helpstr):
    return [PercentileAggregator(round(100*i/q), helpstr) for i in range(1, q)]


vd.aggregator('min', min, 'minimum value')
vd.aggregator('max', max, 'maximum value')
vd.aggregator('avg', mean, 'arithmetic mean of values', type=float)
vd.aggregator('mean', mean, 'arithmetic mean of values', type=float)
vd.aggregator('median', statistics.median, 'median of values')
vd.aggregator('mode', statistics.mode, 'mode of values')
vd.aggregator('sum', vsum, 'sum of values')
vd.aggregator('distinct', set, 'distinct values', type=vlen)
vd.aggregator('count', lambda values: sum(1 for v in values), 'number of values', type=int)
vd.aggregator('list', list, 'list of values', type=anytype)
vd.aggregator('stdev', statistics.stdev, 'standard deviation of values', type=float)

vd.aggregators['q3'] = quantiles(3, 'tertiles (33/66th pctile)')
vd.aggregators['q4'] = quantiles(4, 'quartiles (25/50/75th pctile)')
vd.aggregators['q5'] = quantiles(5, 'quintiles (20/40/60/80th pctiles)')
vd.aggregators['q10'] = quantiles(10, 'deciles (10/20/30/40/50/60/70/80/90th pctiles)')

# since bb29b6e, a record of every aggregator
# is needed in vd.aggregators
for pct in (10, 20, 25, 30, 33, 40, 50, 60, 67, 70, 75, 80, 90, 95, 99):
    vd.aggregators[f'p{pct}'] = PercentileAggregator(pct, f'{pct}th percentile')

class KeyFindingAggregator(Aggregator):
    '''Return the key of the row that results from applying *aggr_func* to *rows*.
        Return None if *rows* is an empty list.
        *aggr_func* takes a list of (value, row) tuples, one for each row in the column,
        excluding rows where the column holds null and error values.
        *aggr_func* must also take the parameters *default* and *key*, as max() does:
        https://docs.python.org/3/library/functions.html#max'''

    def __init__(self, aggr_func, *args, **kwargs):
        self.aggr_func = aggr_func
        super().__init__(*args, **kwargs)

    def aggregate(self, col, rows):
        if not col.sheet.keyCols:
            vd.error('key aggregator function requires one or more key columns')
            return None
        # convert dicts to lists because functions like max() can't compare dicts
        sortkey = lambda t: (t[0], sorted(t[1].items())) if isinstance(t[1], dict) else t
        row = self.aggr_func(col.getValueRows(rows), default=(None, None), key=sortkey)[1]
        return col.sheet.rowkey(row) if row else None

vd.aggregators['keymin'] = KeyFindingAggregator(min, 'keymin', anytype, helpstr='key of the minimum value')
vd.aggregators['keymax'] = KeyFindingAggregator(max, 'keymax', anytype, helpstr='key of the maximum value')


ColumnsSheet.columns += [
    Column('aggregators',
           getter=lambda c,r:r.aggstr,
           setter=lambda c,r,v:setattr(r, 'aggregators', v),
           help='change the metrics calculated in every Frequency or Pivot derived from the source sheet')
]

@Sheet.api
def addAggregators(sheet, cols, aggrnames):
    'Add each aggregator in list of *aggrnames* to each of *cols*. Ignores names that are not valid.'
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
def aggregateTotal(col, agg):
    if agg not in col._aggregatedTotals:
        col._aggregatedTotals[agg] = INPROGRESS
        col._aggregateTotalAsync(agg)
    return col._aggregatedTotals[agg]


@Column.api
@asyncthread
def _aggregateTotalAsync(col, agg):
    col._aggregatedTotals[agg] = agg.aggregate(col, col.sheet.rows)


@Column.api
@asyncthread
def memo_aggregate(col, agg_choices, rows):
    'Show aggregated value in status, and add to memory.'
    for agg_choice in agg_choices:
        agg = vd.aggregators.get(agg_choice)
        if not agg: continue
        aggs = agg if isinstance(agg, list) else [agg]
        for agg in aggs:
            aggval = agg.aggregate(col, rows)
            typedval = wrapply(agg.type or col.type, aggval)
            dispval = col.format(typedval)
            k = col.name+'_'+agg.name
            vd.status(f'{k}={dispval}')
            vd.memory[k] = typedval


@VisiData.property
def aggregator_choices(vd):
    return [
       AttrDict(key=agg, desc=v[0].helpstr if isinstance(v, list) else v.helpstr)
         for agg, v in vd.aggregators.items()
            if not agg.startswith('p')  # skip all the percentiles, user should use q# instead
    ]


@VisiData.api
def chooseAggregators(vd):
    '''Return a list of aggregator name strings chosen or entered by the user. User-entered names may be invalid.'''
    prompt = 'choose aggregators: '
    def _fmt_aggr_summary(match, row, trigger_key):
        formatted_aggrname = match.formatted.get('key', row.key) if match else row.key
        r = ' '*(len(prompt)-3)
        r += f'[:keystrokes]{trigger_key}[/]  '
        r += formatted_aggrname
        if row.desc:
            r += ' - '
            r += match.formatted.get('desc', row.desc) if match else row.desc
        return r

    r = vd.activeSheet.inputPalette(prompt,
            vd.aggregator_choices,
            value_key='key',
            formatter=_fmt_aggr_summary,
            type='aggregators',
            help=vd.help_aggregators,
            multiple=True)

    aggrs = r.split()
    valid_choices = vd.aggregators.keys()
    for aggr in aggrs:
        vd.usedInputs[aggr] += 1
        if aggr not in valid_choices:
            vd.warning(f'aggregator does not exist: {aggr}')
    return aggrs

Sheet.addCommand('+', 'aggregate-col', 'addAggregators([cursorCol], chooseAggregators())', 'add aggregator to current column')
Sheet.addCommand('z+', 'memo-aggregate', 'cursorCol.memo_aggregate(chooseAggregators(), selectedRows or rows)', 'memo result of aggregator over values in selected rows for current column')
ColumnsSheet.addCommand('g+', 'aggregate-cols', 'addAggregators(selectedRows or source[0].nonKeyVisibleCols, chooseAggregators())', 'add aggregators to selected source columns')

vd.addMenuItems('''
    Column > Add aggregator > aggregate-col
''')
