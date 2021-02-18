import re
from visidata import vd, date, asyncthread, VisiData, Progress, Sheet, Column, ItemColumn, deduceType, TypedWrapper
from airtable import Airtable

vd.option('airtable_key', '', 'Airtable API key from https://airtable.com/account')
vd.option('airtable_base', '', 'Airtable base ID from https://airtable.com/api')

@VisiData.api
def open_airtable(vd, p):
    m = re.search(r'(tbl[A-z0-9]{14})/(viw[A-z0-9]{14})', p.given)
    if m:
        return AirtableSheet(m.groups()[0], source=m.groups()[0], view=m.groups()[1])


class AirtableSheet(Sheet):
    rowtype = 'records' # rowdef: dict
    savesToSource = True
    defer = True

    def iterload(self):
        def fieldColumn(field, value):
            from visidata import setitem
            return Column(field,
                expr=field, type=deduceType(value),
                getter=lambda c,r: r['fields'].get(c.expr),
                setter=lambda c,r,v: setitem(r['fields'], c.expr, v))

        self.columns = []
        self.addColumn(ItemColumn('id', 'id', type=str, width=0))
        self.addColumn(ItemColumn('createdTime', 'createdTime', type=date, width=0))

        fields = set()
        airtable = Airtable(vd.options.airtable_base, self.source, vd.options.airtable_key)
        for page in Progress(airtable.get_iter(view=self.view), gerund='loading', total=1):
            for record in page:
                for field, value in record['fields'].items():
                    if field not in fields:
                        self.addColumn(fieldColumn(field, value))
                        fields.add(field)
                yield record

    def newRow(self):
        return {'fields': {}}

    @asyncthread
    def putChanges(self):
        def fields(row, cols, includeNones=False):
            fields = {}
            for col in cols:
                val = col.getTypedValue(row)
                if isinstance(val, TypedWrapper):
                    if includeNones:
                        fields[col.expr] = None
                else:
                    fields[col.expr] = val
            return fields

        def update(row, cols):
            return {'id': row['id'], 'fields': fields(row, cols, includeNones=True)}

        adds, mods, dels = self.getDeferredChanges()
        airtable = Airtable(vd.options.airtable_base, self.source, vd.options.airtable_key)
        with Progress(gerund='inserting', total=3) as prog:
            airtable.batch_insert([fields(r, self.visibleCols) for r in adds.values()])
            prog.addProgress(1)
            prog.gerund = 'updating'
            airtable.batch_update([update(r, m.keys()) for r, m in mods.values()])
            prog.addProgress(1)
            prog.gerund = 'deleting'
            airtable.batch_delete([r['id'] for r in dels.values()])
            prog.addProgress(1)

        self.preloadHook()
        self.reload()
