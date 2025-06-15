import os
import time

from visidata import vd, BaseSheet, Sheet, asyncignore, asyncthread, Path, ScopedSetattr


@BaseSheet.api
@asyncignore
def reload_every(sheet, seconds:int):
    while True:
        # continue reloading till vd.remove() runs, like when the sheet is quit
        if not sheet in vd.sheets:
            break
        vd.sync(sheet.reload())
        time.sleep(seconds)


@BaseSheet.api
@asyncthread
def reload_modified(sheet):
    'Spawn thread to call sheet.reload_rows when sheet.source mtime has changed.'
    p = sheet.source
    assert isinstance(p, Path)
    assert not p.is_url()

    mtime = 0
    while True:
        t = os.stat(p).st_mtime
        if t != mtime:
            mtime = t
            sheet.reload_rows()
        time.sleep(1)


@Sheet.api
@asyncthread
def reload_rows(self):
    'Reload rows from ``self.source``, keeping current columns intact.  Async.'
    with (ScopedSetattr(self, 'loading', True),
          ScopedSetattr(self, 'checkCursor', lambda: True),
          ScopedSetattr(self, 'cursorRowIndex', self.cursorRowIndex)):
            self.beforeLoad()
            try:
                self.loader()
                vd.status("finished loading rows")
            finally:
                self.afterLoad()


BaseSheet.addCommand('', 'reload-every', 'sheet.reload_every(input("reload interval (sec): ", value=1))', 'schedule sheet reload every N seconds') #683
BaseSheet.addCommand('', 'reload-modified', 'sheet.reload_modified()', 'reload sheet when source file modified (tail-like behavior)')  #1686
Sheet.addCommand('z^R', 'reload-rows', 'preloadHook(); reload_rows(); status("reloaded")', 'Reload current sheet leaving current columns intact')

vd.addMenuItems('''
    File > Reload > rows only > reload-rows
    File > Reload > every N seconds > reload-every
    File > Reload > when source modified > reload-modified
''')
