from visidata import BaseSheet, asyncthread


@BaseSheet.api
@asyncthread
def reload_every(sheet, seconds:int):
    import time
    while True:
        sheet.reload()
        time.sleep(seconds)


BaseSheet.addCommand('', 'reload-every', 'sheet.reload_every(input("reload interval (sec): ", value=1))', 'schedule sheet reload every N seconds') #683
