__version__ = '0.9'

from copy import copy

from visidata import Sheet, vd, asyncsingle, cancelThread

@Sheet.api
def dup_search(sheet, cols='cursorCol'):
    vs = copy(sheet)
    vs.name += "_search"
    vs.rows = sheet.rows
    vs.source = sheet
    vs.search = ''

    @asyncsingle
    def live_search_async(val):
        if not val:
            vs.rows = vs.source.rows
        else:
            vs.rows = []
            for i in vd.searchRegex(vs.source, regex=val, columns=cols):
                vs.addRow(vs.source.rows[i])

    def live_search(val):
        vs.draw(vd._scr)
        vd.drawRightStatus(vd._scr, vs)
        val = val.rstrip('\n')
        if val == vs.search:
            return
        vs.search = val
        live_search_async(val, sheet=vs, status=False)

    vd.input("search regex: ", updater=live_search)
    vd.push(vs)
    vs.name = vs.source.name+'_'+vs.search


Sheet.addCommand('^[s', 'dup-search', 'dup_search("cursorCol")')
Sheet.addCommand('g^[s', 'dup-search-cols', 'dup_search("visibleCols")')
