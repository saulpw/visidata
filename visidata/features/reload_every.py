from visidata import vd, BaseSheet, asyncthread


@BaseSheet.api
@asyncthread
def reload_every(sheet, seconds:int):
    import time
    while True:
        sheet.reload()
        time.sleep(seconds)


BaseSheet.addCommand('', 'reload-every', 'sheet.reload_every(input("reload interval (sec): ", value=1))', 'schedule sheet reload every N seconds') #683

vd.addMenuItems('''
    File > Reload > sheet > reload-sheet
    File > Reload > every N seconds > reload-every
''')
