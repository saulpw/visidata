# install the faker module: pip3 install Faker
# copy this file into .visidata/fake.py
# add "import fake" to .visidatarc

# to anonymize a column in vd: do "setcol-fake" with e.g. 'name' 'isbn10' or any of the functions on Faker()

from visidata import vd, Column, Sheet, option, options, asyncthread, Progress, undoEditCells

Sheet.addCommand(None, 'setcol-fake', 'cursorCol.setValuesFromFaker(input("faketype: ", type="faketype"), selectedRows or rows)', undo=undoEditCells)

option('locale', 'en_US', 'default locale to use for Faker', replay=True)

vd.newvals = {None: None}

@Column.api
@asyncthread
def setValuesFromFaker(col, faketype, rows):
    import faker
    fake = faker.Faker(options.locale)
    fakefunc = getattr(fake, faketype)

    vd.newvals[options.null_value] = options.null_value
    for r in Progress(rows):
        v = col.getValue(r)
        if v in vd.newvals:
            newv = vd.newvals[v]
        else:
            newv = fakefunc()
            vd.newvals[v] = newv
        col.setValue(r, newv)
