import re
from visidata import vd, VisiData, Sheet, ItemColumn
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
        for page in airtable.get_iter(view=self.view):
            for record in page:
                if not self.columns:
                    for key, val in record['fields'].items():
                        self.addColumn(ItemColumn(key, key, type=type(val)))
                yield record['fields']
