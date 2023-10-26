''' Plugin for viewing files with appropriate mailcap-specified application.
Add mailcap-view and mailcap-view-selected commands to DirSheet.

mimetype can be given explicitly with `mimetype` option; will be guessed by filename otherwise.

Usage:
   - add `import experimental.mailcap_view` to .visidatarc
   - on the DirSheet, `Ctrl+V` or `gCtrl+V` to view file(s) using mailcap entry for the guessed (or given via options) mimetype
'''

import os
from visidata import vd, DirSheet, SuspendCurses

vd.option('mailcap_mimetype', '', 'force mimetype for sysopen-mailcap')
vd.optalias('mimetype', 'mailcap_mimetype')


@DirSheet.api
def run_mailcap(sheet, p, key='view'):
    import mailcap
    import mimetypes

    mimetype = sheet.options.mailcap_mimetype
    if not mimetype:
        mimetype, encoding = mimetypes.guess_type(str(p))

    if not mimetype:
        vd.fail('no mimetype given and no guess')

    caps = mailcap.getcaps()

    plist = [f'{k}={v}' for k, v in sheet.options.getall('mailcap_').items() if k != 'mailcap_mimetype']
    cmdline, mcap_entry = mailcap.findmatch(caps, mimetype, key=key, filename=str(p), plist=plist)

    with SuspendCurses():
        os.system(cmdline)


DirSheet.addCommand('', 'sysopen-mailcap', 'run_mailcap(cursorRow)', 'open using mailcap entry for current row, guessing mimetype')
DirSheet.addCommand('', 'sysopen-mailcap-selected', 'for r in selectedRows: run_mailcap(r)', 'open selected files in succession, using mailcap')


vd.addMenuItems('''
    File > Open > using mailcap > file at cursor > sysopen-mailcap
    File > Open > using mailcap > selected files > sysopen-mailcap-selected
''')
