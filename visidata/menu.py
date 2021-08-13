import string
import textwrap

from visidata import *


vd.option('show_menu', False, '')
vd.option('color_menu', 'white on 234 black', '')
vd.option('color_menu_inactive', '245 white on 241 black', '')
vd.option('color_menu_active', '223 yellow on black', '')
vd.option('disp_menu_chars', '││──┌┐└┘', 'box characters to use for menus')

vd.activeMenuItems = []


def MenuItem(title, longname='', menus=[]):
    return AttrDict(title=title, menus=menus, longname=longname)


vd.menus = [
    MenuItem('File', menus=[
        MenuItem('New', 'open-new'),
        MenuItem('Open file/url', 'open-file'),
        MenuItem('Save as', 'save-sheet'),
        MenuItem('Commit', 'commit-sheet'),
        MenuItem('Close sheet', 'quit-sheet'),
        MenuItem('Options', menus=[
            MenuItem('All sheets', 'options-global'),
            MenuItem('This sheet', 'options-sheet'),
        ]),
        MenuItem('Exit VisiData', 'quit-all'),
    ]),

    MenuItem('Edit', menus=[
        MenuItem('Undo', 'undo-last'),
        MenuItem('Redo', 'redo-last'),
        MenuItem('Add rows', 'add-rows'),
        MenuItem('Edit', menus=[
            MenuItem('current cell', 'edit-cell'),
            MenuItem('selected cells', 'setcol-input'),
        ]),
        MenuItem('Delete', menus=[
            MenuItem('Current row', 'delete-row'),
            MenuItem('Selected rows', 'delete-selected'),
            MenuItem('Cursor cell', 'delete-cell'),
        ]),
        MenuItem('Copy', menus=[
            MenuItem('selected cells', 'copy-cells'),
            MenuItem('current cells', 'copy-cell'),
        ]),
        MenuItem('Cut', menus=[
            MenuItem('selected cells', 'cut-cells'),
            MenuItem('current cells', 'cut-cell'),
        ]),
        MenuItem('Paste to', menus=[
            MenuItem('selected cells', 'setcol-clipboard'),
            MenuItem('current cell', 'paste-cell'),
        ]),
        MenuItem('Copy to system clipboard', menus=[
            MenuItem('selected cells', 'copy-cells'),
            MenuItem('current cells', 'copy-cell'),
        ]),
    ]),

    MenuItem('View', menus=[
        MenuItem('Statuses', 'open-statuses'),
        MenuItem('All columns', 'columns-all'),
        MenuItem('Errors', menus=[
            MenuItem('recent', 'error-recent'),
            MenuItem('all', 'errors-all'),
            MenuItem('in cell', 'error-cell'),
        ]),
        MenuItem('Search', menus=[
            MenuItem('current column', 'search-col'),
            MenuItem('visible columns', 'search-cols'),
            MenuItem('key columns', 'search-keys'),
            MenuItem('by Python expr', 'search-expr'),
            MenuItem('again', 'search-next'),
        ]),
        MenuItem('Reverse Search', menus=[
            MenuItem('current column', 'searchr-col'),
            MenuItem('visible columns', 'searchr-cols'),
            MenuItem('key columns', 'searchr-keys'),
            MenuItem('by Python expr', 'searchr-expr'),
            MenuItem('again', 'searchr-next'),
        ]),
        MenuItem('Split window',menus=[
            MenuItem('in half', 'splitwin-half'),
            MenuItem('in percent', 'splitwin-input'),
            MenuItem('unsplit', 'splitwin-close'),
        ]),
    ]),

    MenuItem('Sheet', menus=[
        MenuItem('Transpose', 'transpose'),
        MenuItem('Melt', 'melt'),
        MenuItem('Columns', 'columns-sheet'),
    ]),

    MenuItem('Column', menus=[
        MenuItem('Hide', 'hide-col'),
        MenuItem('Type as', menus=[
            MenuItem('No type', 'type-any'),
            MenuItem('String', 'type-str'),
            MenuItem('Integer', 'type-int'),
            MenuItem('Float', 'type-float'),
            MenuItem('SI Float', 'type-floatsi'),
            MenuItem('Dirty float', 'type-currency'),
            MenuItem('Date', 'type-date'),
            MenuItem('Length', 'type-len'),
        ]),
        MenuItem('Toggle as key', 'key-col'),
        MenuItem('Sort by', menus=[
            MenuItem('Current column only', menus=[
                MenuItem('Ascending', 'sort-asc'),
                MenuItem('Descending', 'sort-desc'),
            ]),
            MenuItem('Current column too', menus=[
                MenuItem('Ascending', 'sort-asc-add'),
                MenuItem('Descending', 'sort-desc-add'),
            ]),
            MenuItem('Key columns', menus=[
                MenuItem('Ascending', 'sort-keys-asc'),
                MenuItem('Descending', 'sort-keys-desc'),
            ]),
        ]),
        MenuItem('Expand', 'expand-col'),
        MenuItem('Contract', 'contract-col'),
        MenuItem('Split', 'split-col'),
        MenuItem('Transform', 'setcol-subst'),
        MenuItem('Add column', menus=[
            MenuItem('empty', 'addcol-new'),
            MenuItem('regex capture', 'addcol-capture'),
            MenuItem('regex transform', 'addcol-subst'),
            MenuItem('Python expr', 'addcol-expr'),
            MenuItem('increment', 'addcol-incr'),
            MenuItem('shell', 'addcol-shell'),
        ]),
    ]),

    MenuItem('Select', menus=[
        MenuItem('Current row', 'select-row'),
        MenuItem('All rows', 'select-rows'),
        MenuItem('Like current cell', 'select-equal-cell'),
        MenuItem('Equal to current cell', 'select-exact-cell'),
        MenuItem('From top', 'select-before'),
        MenuItem('To bottom', 'select-after'),
        MenuItem('By Python expr', 'select-expr'),
        MenuItem('By regex', menus=[
            MenuItem('Current column', 'select-col-regex'),
            MenuItem('All columns', 'select-cols-regex'),
        ]),
        MenuItem('Errors', menus=[
            MenuItem('Current column', 'select-error-col'),
            MenuItem('Any column', 'select-error'),
        ]),
    ]),

    MenuItem('Tools', menus=[
        MenuItem('Plugins', 'open-plugins'),
        MenuItem('Command log', 'cmdlog-all'),
    ]),

    MenuItem('Help', menus=[
        MenuItem('Quick reference', 'sysopen-help'),
        MenuItem('Open command list', 'help-commands'),
        MenuItem('Tutorial', 'open-tutorial'),
        MenuItem('Version', 'show-version'),
    ]),
]


@VisiData.api
def drawSubmenu(vd, scr, sheet, y, x, menus, level, disp_menu_chars=''):
    if not menus:
        return
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_chars

    vd.activeMenuItems[level] %= len(menus)

    w = max(len(item.title) for item in menus)

    # draw borders before/under submenus
    if level > 1:
        scr.addstr(y-1, x, tl+ts*(w+2)+tr, colors.color_menu)  # top

    scr.addstr(y+len(menus), x, bl+bs*(w+2)+br, colors.color_menu) #  bottom

    for i, item in enumerate(menus):
        scr.addstr(y+i, x, ls, colors.color_menu)
        if i == vd.activeMenuItems[level]:
            attr = colors.color_menu_active
            if level+1 < len(vd.activeMenuItems):
                vd.drawSubmenu(scr, sheet, y+i, x+w+3, item.menus, level+1, disp_menu_chars=disp_menu_chars)
        else:
            attr = colors.color_menu

        title = ' '+item.title
        titlenote = ' '
        if item.menus:
            titlenote = '»'
        else:
            cmd = sheet.getCommand(item.longname)
            if cmd and cmd.execstr:
                if 'push(' in cmd.execstr:
                    titlenote = '∴'
                if 'input' in cmd.execstr:
                    title += '…'

        title += ' '*(w-len(item.title)) # padding

        scr.addstr(y+i, x+1, title+titlenote, attr)
        scr.addstr(y+i, x+3+w, ls, colors.color_menu)


@VisiData.api
def drawMenu(vd, scr, sheet):
    h, w = scr.getmaxyx()
    scr.addstr(0, 0, ' '*(w-1), colors.color_menu)
    disp_menu_chars = sheet.options.disp_menu_chars
    x = 1
    for i, item in enumerate(vd.menus):
        if vd.activeMenuItems and i == vd.activeMenuItems[0]:
            attr = colors.color_menu_active
            vd.drawSubmenu(scr, sheet, 1, x, item.menus, 1, disp_menu_chars)
        else:
            attr = colors.color_menu

        scr.addstr(0, x, ' '+item.title+' ', attr)
        scr.addstr(0, x+1, item.title[0], attr | curses.A_UNDERLINE)
        vd.onMouse(scr, 0, x, 1, len(item),
                BUTTON1_PRESSED=lambda y,x,key,i=i: vd.pressMenu(i),
                BUTTON1_RELEASED=lambda y,x,key,i=i: vd.runMenu(i))
        x += len(item.title)+2

    if not vd.activeMenuItems:
        return

    currentItem = vd
    for i in vd.activeMenuItems:
        currentItem = currentItem.menus[i]

    cmd = sheet.getCommand(currentItem.longname)

    if not cmd or not cmd.helpstr:
        return

    # help box
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_chars
    helpw = min(76, w)
    helplines = textwrap.wrap(cmd.helpstr, width=helpw-4)
    y = h-len(helplines)-2
    scr.addstr(y, 2, tl+ts*(helpw-2)+tr, colors.color_menu)
    scr.addstr(h-1, 2, bl+bs*(helpw-2)+br, colors.color_menu)
    for i, line in enumerate(helplines):
        scr.addstr(h-len(helplines)-1+i, 2, ls+' '+line+' '*(helpw-len(line)-3)+rs, colors.color_menu)

    mainbinding = HelpSheet().revbinds.get(cmd.longname, [None])[0]
    if mainbinding:
        scr.addstr(y, 4, ' '+vd.prettybindkey(mainbinding or '(unbound)')+' ', colors.color_menu_active)
    scr.addstr(y, 16, ' '+cmd.longname+' ', colors.color_menu)


@VisiData.api
def prettybindkey(vd, k):
    k = k[:-1].replace('^', 'Ctrl+')+k[-1]
    if k[-1] in string.ascii_uppercase and '+' not in k and '_' not in k:
        k = k[:-1] + 'Shift+' + k[-1]

    return {
        'Ctrl+I': 'Tab',
        'Ctrl+J': 'Enter',
        ' ': 'Space',
    }.get(k, k).strip()


@VisiData.api
def runMenu(vd, i):
    old_show_menu = vd.options.show_menu

    vd.options.show_menu=True
    vd.activeMenuItems = [i, 0]

    while True:
        vd.draw_all()

        k = vd.getkeystroke(vd.scrMenu, vd.activeSheet)

        currentItem = vd
        for i in vd.activeMenuItems:
            currentItem = currentItem.menus[i]

        if k in ['^C', '^Q', '^[', 'q']: break
        elif k in ['KEY_RIGHT', 'l']:
            if currentItem.menus:
                vd.activeMenuItems.append(0)
            else:
                vd.activeMenuItems = [vd.activeMenuItems[0]+1, 0]

        elif k in ['KEY_LEFT', 'h']:
            if len(vd.activeMenuItems) > 2:
                vd.activeMenuItems.pop(-1)
            else:
                vd.activeMenuItems = [vd.activeMenuItems[0]-1, 0]

        elif k in ['KEY_DOWN', 'j']:
            vd.activeMenuItems[-1] += 1

        elif k in ['KEY_UP', 'k']:
            vd.activeMenuItems[-1] -= 1

        elif k in [ENTER, ' ']:
            if currentItem.menus:
                vd.activeMenuItems.append(0)
            else:
                vd.activeSheet.execCommand(currentItem.longname)
                break

        vd.activeMenuItems[0] %= len(vd.menus)

    vd.activeMenuItems = []
    vd.options.show_menu=old_show_menu


@VisiData.api
def pressMenu(vd, i):
    vd.status(i)


def open_mnu(p):
    return MenuSheet(p.name, source=p)


vd.save_mnu=vd.save_tsv

class MenuSheet(VisiDataMetaSheet):
    rowtype='labels' # { .x .y .text .color .command .input }


class MenuCanvas(BaseSheet):
    rowtype='labels'
    def click(self, r):
        vd.replayOne(vd.cmdlog.newRow(sheet=self.name, col='', row='', longname=r.command, input=r.input))

    def reload(self):
        self.rows = self.source.rows

    def draw(self, scr):
        vd.clearCaches()
        for r in Progress(self.source.rows):
            x, y = map(int, (r.x, r.y))
            clipdraw(scr, y, x, r.text, colors[r.color])
            vd.onMouse(scr, y, x, 1, len(r.text), BUTTON1_RELEASED=lambda y,x,key,r=r,sheet=self: sheet.click(r))


MenuSheet.addCommand('z.', 'disp-menu', 'vd.push(MenuCanvas(name, "disp", source=sheet))', '')
BaseSheet.addCommand('^[', 'open-menu', 'runMenu(0)', '')
