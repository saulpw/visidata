'''
Plugin for viewing files with appropriate mailcap-specified application.
Add mailcap-view and mailcap-view-selected commands to DirSheet.

mimetype can be given explicity with `mimetype` option; will be guessed by filename otherwise.

Usage:
   1. copy to plugins dir
   2. add `import plugins.vmailcap` to .visidatarc or .vlsrc
   3. press Ctrl+V or g-Ctrl+V to view file(s) as desired.
'''

__name__ = 'vmailcap'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__version__ = 0.9

import os
from visidata import DirSheet, option, options, SuspendCurses, fail

option('mimetype', '', 'mimetype to be used with mailcap')

@DirSheet.api
def run_mailcap(sheet, p, key):
    import mailcap
    import mimetypes

    mimetype = options.mimetype
    if not mimetype:
        mimetype, encoding = mimetypes.guess_type(str(p))

    if not mimetype:
        fail('no mimetype given and no guess')

    caps = mailcap.getcaps()

    cmdline, mcap_entry = mailcap.findmatch(caps, mimetype, key=key, filename=str(p))
    with SuspendCurses():
        os.system(cmdline)


DirSheet.addCommand('^V', 'mailcap-view', 'run_mailcap(cursorRow, "view")')
DirSheet.addCommand('g^V', 'mailcap-view-selected', 'for r in selectedRows: run_mailcap(r, "view")')
