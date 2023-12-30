# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

import json

from visidata import vd, Column, Sheet, asyncthread, Progress, VisiData

vd.option('faker_locale', 'en_US', 'default locale to use for Faker', replay=True)
vd.option('faker_extra_providers', None, 'list of additional Provider classes to load via add_provider()', replay=True)
vd.option('faker_salt', '', 'Use a non-empty string to enable deterministic fakes')

def addFakerProviders(fake, providers):
    '''
    Add custom providers to Faker. Provider classes typically derive from
    faker.providers.BaseProvider, so check for that here. This helps to
    highlight likely misconfigurations instead of hiding them.

    See also: https://faker.readthedocs.io/en/master/communityproviders.html

    fake: Faker object
    providers: List of provider classes to add
    '''
    faker = vd.importExternal('faker', 'Faker')
    if isinstance(providers, str):
        providers = [ getattr(faker.providers, p) for p in providers.split() ]

    if not isinstance(providers, list):
        vd.fail('options.faker_extra_providers must be a list')

    for provider in providers:
        if not issubclass(provider, faker.providers.BaseProvider):
            vd.warning('"{}" not a Faker Provider'.format(provider.__name__))
            continue
        fake.add_provider(provider)

@Column.api
@asyncthread
def setValuesFromFaker(col, faketype, rows):
    faker = vd.importExternal('faker', 'Faker')
    fake = faker.Faker(col.sheet.options.faker_locale)
    if col.sheet.options.faker_extra_providers:
        addFakerProviders(fake, col.sheet.options.faker_extra_providers)
    fakefunc = getattr(fake, faketype, None) or vd.fail(f'no such faker "{faketype}"')

    fakeMap = {}
    fakeMap[None] = None
    fakeMap[col.sheet.options.null_value] = col.sheet.options.null_value

    vd.addUndoSetValues([col], rows)
    salt = col.sheet.options.faker_salt

    for r in Progress(rows):
        v = col.getValue(r)
        if v in fakeMap:
            newv = fakeMap[v]
        else:
            if salt:
                # Reset the Faker seed for each value. For a given salt string,
                # the same cell value will always generate the same fake value.
                fake.seed_instance(json.dumps(v) + salt)
            newv = fakefunc()
            fakeMap[v] = newv
        col.setValue(r, newv)


Sheet.addCommand(None, 'setcol-fake', 'cursorCol.setValuesFromFaker(input("faketype: ", type="faketype"), selectedRows)', 'replace values in current column for selected rows with fake values')
