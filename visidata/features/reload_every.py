import os
import time

from visidata import vd, BaseSheet, Sheet, asyncignore, asyncsingle_queue, Path, ScopedSetattr, ExpectedException


@BaseSheet.api
def startReload(sheet, reloadfunc):
    'Return thread from reloadfunc(), or None if a command is still running on *sheet*.'
    if sheet.lastCommandThreads:
        return None
    try:
        return reloadfunc()
    except ExpectedException:  # race: a command can start after the check
        return None


@BaseSheet.api
@asyncignore
def reload_every(sheet, seconds:int):
    while True:
        # continue reloading till vd.remove() runs, like when the sheet is quit
        if sheet not in vd.sheets:
            break
        t = sheet.startReload(sheet.reload)
        if t:
            vd.sync(t)
        time.sleep(seconds)


@BaseSheet.api
@asyncignore
def reload_modified(sheet):
    'Spawn thread to call sheet.reload_rows when sheet.source mtime has changed.'
    p = sheet.source
    assert isinstance(p, Path)
    assert not p.is_url()

    mtime = 0
    while True:
        if sheet not in vd.sheets:
            break
        t = os.stat(p).st_mtime
        if t != mtime and sheet.startReload(sheet.reload_rows):
            mtime = t
        time.sleep(1)


@Sheet.api
@asyncsingle_queue
def reload_rows(self):
    '''Reload rows from ``self.source``, keeping current columns intact.  Async. If previous calls are running, waits for them to finish.'''
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
Sheet.addCommand('zCtrl+R', 'reload-rows', 'preloadHook(); reload_rows(); status("reloaded")', 'Reload current sheet leaving current columns intact')

vd.addMenuItems('''
    File > Reload > rows only > reload-rows
    File > Reload > every N seconds > reload-every
    File > Reload > when source modified > reload-modified
''')
