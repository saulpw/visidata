from visidata import vd, Sheet, VisiData, FreqTableSheet, BaseSheet, asyncthread

vd.options.disp_menu_fmt = '|  VisiData {vd.version} | {vd.motd}'

vd.addMenuItem('Help', '+VisiData Plus', 'help-vdplus')

# HTML("<html>...") and JSON('{"k":"v"...}')
@VisiData.lazy_property
def utf8_parser(vd):
    from lxml import etree
    return etree.HTMLParser(encoding='utf-8')

@VisiData.api
def HTML(vd, s):
    import lxml.html
    return lxml.html.etree.fromstring(s, parser=vd.utf8_parser)

@VisiData.api
def JSON(vd, s):
    import json
    return json.loads(s)


Sheet.addCommand('', 'addcol-source', 'source.addColumn(copy(cursorCol))', 'add copy of current column to source sheet')  #988  frosencrantz
FreqTableSheet.addCommand('', 'select-first', 'for r in rows: source.select([r.sourcerows[0]])', 'select first source row in each bin')

Sheet.addCommand('', 'clean-names', '''
options.clean_names = True;
for c in visibleCols:
    c.name = c.name
''', 'set options.clean_names on sheet and clean visible column names')

BaseSheet.addCommand('', 'reload-every', 'sheet.reload_every(input("reload interval (sec): ", value=1))') #683


@BaseSheet.api
@asyncthread
def reload_every(sheet, seconds:int):
    import time
    while True:
        sheet.reload()
        time.sleep(seconds)


