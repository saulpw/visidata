# install the faker module: pip3 install Faker
# copy this file into .visidata/fake.py
# add "import fake" to .visidatarc

# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

from visidata import VisiData, Sheet, replayableOption, asyncthread, isNullFunc, options, Progress, undoEditCells

Sheet.addCommand(None, 'setcol-fake', 'fakeCol(input("faketype: ", type="faketype"), cursorCol, selectedRows or rows)', undo=undoEditCells)

replayableOption('locale', 'en_US', 'default locale to use for Faker')

@VisiData.api
@asyncthread
def fakeCol(vd, faketype, col, rows):
    import faker
    fake = faker.Faker(options.locale)
    fakefunc = getattr(fake, faketype)

    isNull = isNullFunc()
    newvals = {None: None}
    newvals[options.null_value] = options.null_value
    for r in Progress(rows):
        v = col.getValue(r)
        if v in newvals:
            newv = newvals[v]
        else:
            newv = fakefunc()
            newvals[v] = newv
        col.setValue(r, newv)
