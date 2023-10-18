import os
import time

from visidata import vd, BaseSheet, asyncthread, Path


@BaseSheet.api
@asyncthread
def reload_every(sheet, seconds:int):
    while True:
        sheet.reload()
        time.sleep(seconds)


@BaseSheet.api
@asyncthread
def reload_modified(sheet):
    'Spawn thread to call sheet.reload when sheet.source mtime has changed.'
    p = sheet.source
    assert isinstance(p, Path)
    assert not p.is_url()

    mtime = os.stat(p).st_mtime
    while True:
        time.sleep(1)
        t = os.stat(p).st_mtime
        if t != mtime:
            mtime = t
            sheet.reload()


BaseSheet.addCommand('', 'reload-every', 'sheet.reload_every(input("reload interval (sec): ", value=1))', 'schedule sheet reload every N seconds') #683
BaseSheet.addCommand('', 'reload-modified', 'sheet.reload_modified()', 'reload sheet when source file modified')  #1686

vd.addMenuItems('''
    File > Reload > sheet > reload-sheet
    File > Reload > every N seconds > reload-every
    File > Reload > when source modified > reload-modified
''')
