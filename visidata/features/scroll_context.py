'''
Enables two functions:
1. options.disp_scroll_context: the minimum number of lines to keep visible above and below the cursor when scrolling
2. toggle-scrollfix: Lock the cursor to a particular row number in the view

Allows the user to fix the position on the page where they would like the
cursor to "stick". Helps to provide context about surrounding rows when
near the top and bottom of the page.

Usage: scroll a few lines down, `toggle-scrollfix' and scroll again!

NOTE:
    - disables scroll-middle command (zz)
'''

__author__ = 'Geekscrapy'
__version__ = '1.2'

from visidata import vd, Sheet

vd.option('disp_scroll_context', 0, 'minimum number of lines to keep visible above/below cursor when scrolling')
vd.optalias('disp_scrolloff', 'disp_scroll_context')

@Sheet.after
def checkCursor(sheet):
    nctx = sheet.options.disp_scroll_context
    if nctx:
        if nctx >= int(sheet.nScreenRows/2):
            if sheet.cursorRowIndex+1 > int(sheet.nScreenRows/2):
                sheet.topRowIndex = sheet.cursorRowIndex - int(sheet.nScreenRows/2)
        else:
            if sheet.cursorRowIndex-sheet.topRowIndex < nctx:
                sheet.topRowIndex = max(0, sheet.cursorRowIndex-nctx)

            if sheet.bottomRowIndex-sheet.cursorRowIndex < nctx:
                sheet.bottomRowIndex = sheet.cursorRowIndex+nctx

    nfix = getattr(sheet, 'disp_scrollfix', 0)
    if nfix > 0:
        cursorViewIndex = sheet.cursorRowIndex - sheet.topRowIndex
        if cursorViewIndex > nfix:
            sheet.topRowIndex += abs(nfix - cursorViewIndex)
        if cursorViewIndex < nfix and sheet.topRowIndex > 0:
            sheet.topRowIndex -= abs(nfix - cursorViewIndex)


@Sheet.api
def toggle_scrollfix(sheet):
    if getattr(sheet, 'disp_scrollfix', -1) >= 0:
        sheet.disp_scrollfix = -1
        vd.status("cursor unlocked")
    else:
        sheet.disp_scrollfix = sheet.cursorRowIndex - sheet.topRowIndex
        vd.status(f"cursor locked to screen row {sheet.disp_scrollfix}")


Sheet.addCommand('', 'toggle-scrollfix', 'toggle_scrollfix()', helpstr='toggle cursor lock to current screen row')


vd.addMenuItems('''View > Toggle display > lock cursor to screen row > toggle-scrollfix''')
