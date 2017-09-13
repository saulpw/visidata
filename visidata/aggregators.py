import collections
from visidata import *

globalCommand('+', 'addAggregator([cursorCol], chooseOne(aggregators))', 'add aggregator for this column')
globalCommand('z+', 'status(chooseOne(aggregators)(cursorCol.values(selectedRows or rows)))', 'aggregate selected rows in this column')

aggregators = collections.OrderedDict()

def aggregator(name, type, func):
    'Define aggregator'
    def _func(values):  # wrap builtins so they can have a .type
        return func(values)
    _func.type = type
    _func.__name__ = name
    aggregators[name] = _func

aggregator('min', None, min)
aggregator('max', None, max)
aggregator('avg', float, lambda values: float(sum(values))/len(values))
aggregator('sum', None, sum)
aggregator('distinct', int, lambda values: len(set(values)))
aggregator('count', int, len)

ColumnsSheet.commands += [
    Command('g+', 'addAggregator(selectedRows or source.nonKeyVisibleCols, chooseOne(aggregators))', 'add aggregator to all selected source columns'),
]
ColumnsSheet.columns += [
        Column('aggregators',
               getter=lambda r: ' '.join(x.__name__ for x in getattr(r, 'aggregators', [])),
               setter=lambda s,c,r,v: setattr(r, 'aggregators', list(aggregators[k] for k in v.split())))
]

def addAggregator(cols, aggr):
    for c in cols:
        if not hasattr(c, 'aggregators'):
            c.aggregators = []
        c.aggregators += [aggr]

addGlobals(globals())
