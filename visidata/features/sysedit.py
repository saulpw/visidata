from copy import copy
from visidata import vd, asyncthread, Path, Sheet, IndexSheet


@Sheet.api
def syseditCells(sheet, cols, rows, filetype=None):
    filetype = filetype or vd.input("edit %d %s as filetype: " % (len(rows), sheet.rowtype), value=sheet.options.save_filetype or 'tsv')
    vd.sync(sheet.syseditCells_async(cols, rows, filetype))


@Sheet.api
@asyncthread
def syseditCells_async(sheet, cols, rows, filetype=None):
    vs = copy(sheet)
    vs.rows = rows or vd.fail('no %s selected' % sheet.rowtype)
    vs.columns = cols

    import tempfile
    with tempfile.NamedTemporaryFile() as temp:
        temp.close()  #2118
        p = Path(temp.name)

        vd.status(f'copying {vs.nRows} {vs.rowtype} to {p} as {filetype}')
        vd.sync(vd.saveSheets(p, vs))

        tempvs = vd.openSource(p, filetype=filetype)

        vd.launchExternalEditorPath(p)
        tempvs.source = p
        vd.sync(tempvs.ensureLoaded())

        while isinstance(tempvs, IndexSheet):
            vd.sync(tempvs.ensureLoaded())
            tempvs = tempvs.rows[0]

        for col in sheet.visibleCols:
            tempcol = tempvs.colsByName.get(col.name)
            if not tempcol: # column not in edited version
                continue
            col.setValuesTyped(rows, *[tempcol.getTypedValue(r) for r in tempvs.rows])


Sheet.addCommand('g^O', 'sysedit-selected', 'syseditCells(visibleCols, onlySelectedRows)', 'edit rows in $EDITOR')
