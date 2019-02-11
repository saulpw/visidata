# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

from visidata import vd, Column, Sheet, option, options, asyncthread, Progress, undoEditCells

__version__ = '0.9'

option('locale', 'en_US', 'default locale to use for Faker', replay=True)

vd.fakeMap = {}

@Column.api
@asyncthread
def setValuesFromFaker(col, faketype, rows):
    import faker
    fake = faker.Faker(options.locale)
    fakefunc = getattr(fake, faketype, None) or error('no such faker function')

    vd.fakeMap[None] = None
    vd.fakeMap[options.null_value] = options.null_value

    for r in Progress(rows):
        v = col.getValue(r)
        if v in vd.fakeMap:
            newv = vd.fakeMap[v]
        else:
            newv = fakefunc()
            vd.fakeMap[v] = newv
        col.setValue(r, newv)


Sheet.addCommand(None, 'setcol-fake', 'cursorCol.setValuesFromFaker(input("faketype: ", type="faketype"), selectedRows or rows)', undo=undoEditCells)
Sheet.addCommand(None, 'reset-fake', 'vd.fakeMap.clear()')
