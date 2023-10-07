from visidata import Sheet, Column, DisplayWrapper


@Column.api
def displayer_url(self, dw:DisplayWrapper, width=None):
    'Display cell text as clickable url'
    yield ('onclick '+dw.text, dw.text)


Sheet.addCommand("", "type-url", "sheet.cursorCol.displayer = 'url'", "set column to open URLs in $BROWSER on mouse click")
Sheet.addCommand("", "open-url", "vd.launchBrowser(sheet.cursorValue)", "open current cursor value in $BROWSER")
