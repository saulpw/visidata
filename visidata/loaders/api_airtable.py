import re
import os

from visidata import vd, date, asyncthread, VisiData, Progress, Sheet, Column, ItemColumn, deduceType, TypedWrapper, setitem, AttrDict


vd.option('airtable_auth_token', '', 'Airtable API key from https://airtable.com/account')

airtable_regex = r'^https://airtable.com/(app[A-Za-z0-9]+)/(tbl[A-Za-z0-9]+)/?(viw[A-z0-9]+)?'

@VisiData.api
def guessurl_airtable(vd, p, response):
    m = re.search(airtable_regex, p.given)
    if m:
        return dict(filetype='airtable', _likelihood=10)


@VisiData.api
def open_airtable(vd, p):
    pyairtable = vd.importExternal('pyairtable')

    token = os.environ.get('AIRTABLE_AUTH_TOKEN') or vd.options.airtable_auth_token
    if not token:
        vd.requireOptions('airtable_auth_token', help='https://support.airtable.com/docs/creating-and-using-api-keys-and-access-tokens')

    m = re.search(airtable_regex, p.given)
    if not m:
        vd.fail('invalid airtable url')

    app, tbl, viw = m.groups()
    return AirtableSheet('airtable', source=p,
                         airtable_auth_token=token,
                         airtable_base=app,
                         airtable_table=tbl,
                         airtable_view=viw)


class AirtableSheet(Sheet):
    guide = '''
        # Airtable
        This sheet is a read-only download of all records in a table at _airtable.com_.
    '''
    rowtype = 'records'  # rowdef: dict

    columns = [
        ItemColumn('id', 'id', type=str, width=0),
        ItemColumn('createdTime', 'createdTime', type=date, width=0)
    ]

    def iterload(self):
        self.fields = set()

        for page in self.api.iterate(self.airtable_base, self.airtable_table, view=self.airtable_view):
            for row in page:
                yield row

                for field, value in row['fields'].items():
                    if field not in self.fields:
                        col = ItemColumn('fields.'+field, type=deduceType(value))
                        self.addColumn(col)
                        self.fields.add(field)

    def newRow(self):
        return AttrDict(fields=AttrDict())


@AirtableSheet.lazy_property
def api(self):
    import pyairtable
    return pyairtable.Api(self.airtable_auth_token)
