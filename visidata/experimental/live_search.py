from copy import copy

from visidata import Sheet, vd, asyncsingle

@Sheet.api
def dup_search(sheet, cols='cursorCol'):
    vs = copy(sheet)
    vs.name += "_search"
    vs.rows = sheet.rows
    vs.source = sheet
    vs.search = ''

    @asyncsingle
    def live_search_async(val, status=False):
        if not val:
            vs.rows = vs.source.rows
        else:
            vs.rows = []
            for i in vd.searchRegex(vs.source, regex=val, columns=cols, printStatus=status):
                vs.addRow(vs.source.rows[i])

    def live_search(val):
        vs.draw(vs._scr)
        vd.drawRightStatus(vs._scr, vs)
        val = val.rstrip('\n')
        if val == vs.search:
            return
        vs.search = val
        live_search_async(val, sheet=vs, status=False)

    vd.input("search regex: ", updater=live_search)
    vd.push(vs)
    vs.name = vs.source.name+'_'+vs.search


Sheet.addCommand('^[s', 'dup-search', 'dup_search("cursorCol")', 'search for regex forwards in current column, creating duplicate sheet with matching rows live')
Sheet.addCommand('g^[s', 'dup-search-cols', 'dup_search("visibleCols")', 'search for regex forwards in all columns, creating duplicate sheet with matching rows live')
