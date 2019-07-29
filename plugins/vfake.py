# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

from visidata import vd, Column, Sheet, option, options, asyncthread, Progress, undoEditCells

__version__ = '0.9'

option('locale', 'en_US', 'default locale to use for Faker', replay=True)

@Column.api
@asyncthread
def setValuesFromFaker(col, faketype, rows):
    import faker
    fake = faker.Faker(options.locale)
    fakefunc = getattr(fake, faketype, None) or vd.error('no such faker function')

    fakeMap = {}
    fakeMap[None] = None
    fakeMap[options.null_value] = options.null_value

    for r in Progress(rows):
        v = col.getValue(r)
        if v in fakeMap:
            newv = fakeMap[v]
        else:
            newv = fakefunc()
            fakeMap[v] = newv
        col.setValue(r, newv)


Sheet.addCommand(None, 'setcol-fake', 'cursorCol.setValuesFromFaker(input("faketype: ", type="faketype"), selectedRows)', undo=undoEditCells)
