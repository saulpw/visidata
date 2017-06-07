from visidata import Sheet

class SheetBlaze(Sheet):
    """Open a dataset via Blaze, either stored in spreadsheets/ or from URL."""
    def __init__(self, name, data, src):
        super().__init__(name, src)
        self.columns = ArrayNamedColumns(data.fields)
        self.rows = list(data)

def openUrl(url):
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if m:
        return open_gspreadsheet(Path(m.group(1)))

    import blaze
    import datashape; datashape.coretypes._canonical_string_encodings.update({"utf8_unicode_ci": "U8"})
    fp = blaze.data(url)
    vs = SheetList(url, [getattr(fp, tblname) for tblname in fp.fields], url)
    vs.command(Key.ENTER, 'vd.push(SheetBlaze(cursorRow.name, cursorRow, sheet))', 'open this table')
    return vs

