# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

from visidata import vd, Column, Sheet, option, options, asyncthread, Progress

__version__ = '0.9'

option('locale', 'en_US', 'default locale to use for Faker', replay=True)

# See also: https://faker.readthedocs.io/en/master/communityproviders.html
option('vfake_extra_providers', [], 'list of additional Provider classes to load via add_provider()', replay=True)

@Column.api
@asyncthread
def setValuesFromFaker(col, faketype, rows):
    import faker
    fake = faker.Faker(options.locale)
    invalid_provider_warning = 'Custom vfake provider "{}" is not a valid Faker Provider class, skipping add'
    for provider in options.vfake_extra_providers:
        if not issubclass(provider, faker.providers.BaseProvider):
            vd.warning(invalid_provider_warning.format(provider.__name__))
            continue
        fake.add_provider(provider)
    fakefunc = getattr(fake, faketype, None) or vd.error('no such faker function')

    fakeMap = {}
    fakeMap[None] = None
    fakeMap[options.null_value] = options.null_value

    vd.addUndoSetValues([col], rows)
    for r in Progress(rows):
        v = col.getValue(r)
        if v in fakeMap:
            newv = fakeMap[v]
        else:
            newv = fakefunc()
            fakeMap[v] = newv
        col.setValue(r, newv)


Sheet.addCommand(None, 'setcol-fake', 'cursorCol.setValuesFromFaker(input("faketype: ", type="faketype"), selectedRows)')
