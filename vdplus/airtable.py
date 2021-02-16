import re
from visidata import vd, date, VisiData, Sheet, Column, ItemColumn, deduceType
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
    def iterload(self):
        airtable = Airtable(vd.options.airtable_base, self.source, vd.options.airtable_key)
        self.columns = []
        self.addColumn(ItemColumn('id', 'id', type=str, width=0))
        self.addColumn(ItemColumn('createdTime', 'createdTime', type=date, width=0))
        fields = set()
        for page in airtable.get_iter(view=self.view):
            for record in page:
                for field, value in record['fields'].items():
                    if field not in fields:
                        self.addColumn(Column(field, expr=field, type=deduceType(value), getter=lambda c,r: r['fields'].get(c.expr)))
                        fields.add(field)
                yield record
