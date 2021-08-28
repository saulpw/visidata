import string
import textwrap

from visidata import *


vd.option('disp_menu', True, 'show menu on top line when not active')
vd.option('color_menu', 'white on 234 black', 'color of menu items in general')
vd.option('color_menu_active', '223 yellow on black', 'color of active menu submenus/item')
vd.option('disp_menu_boxchars', '││──┌┐└┘', 'box characters to use for menus')
vd.option('disp_menu_more', '»', 'command submenu indicator')
vd.option('disp_menu_push', '⎘', 'indicator if command pushes sheet onto sheet stack')
vd.option('disp_menu_input', '…', 'indicator if input required for command')

vd.activeMenuItems = []
vd.menuRunning = False


def Menu(title, *args):
    if len(args) > 1:
        return AttrDict(title=title, menus=args, longname='')
    else:
        return AttrDict(title=title, menus=[], longname=args[0])


vd.menus = [
    Menu('File',
        Menu('New', 'open-new'),
        Menu('Open file/url', 'open-file'),
        Menu('Rename sheet', 'rename-sheet'),
        Menu('Save as', 'save-sheet'),
        Menu('Commit', 'commit-sheet'),
        Menu('Options',
            Menu('All sheets', 'options-global'),
            Menu('This sheet', 'options-sheet'),
        ),
        Menu('Quit',
            Menu('Top sheet', 'quit-sheet'),
            Menu('All sheets', 'quit-all'),
        ),
    ),

    Menu('Edit',
        Menu('Undo', 'undo-last'),
        Menu('Redo', 'redo-last'),
        Menu('Add rows', 'add-rows'),
        Menu('Edit',
            Menu('current cell', 'edit-cell'),
            Menu('selected cells', 'setcol-input'),
        ),
        Menu('Delete',
            Menu('Current row', 'delete-row'),
            Menu('Selected rows', 'delete-selected'),
            Menu('Cursor cell', 'delete-cell'),
        ),
        Menu('Copy',
            Menu('selected cells', 'copy-cells'),
            Menu('current cells', 'copy-cell'),
        ),
        Menu('Cut',
            Menu('selected cells', 'cut-cells'),
            Menu('current cells', 'cut-cell'),
        ),
        Menu('Paste to',
            Menu('selected cells', 'setcol-clipboard'),
            Menu('current cell', 'paste-cell'),
        ),
        Menu('Copy to system clipboard',
            Menu('selected cells', 'copy-cells'),
            Menu('current cells', 'copy-cell'),
        ),
    ),

    Menu('View',
        Menu('Statuses', 'open-statuses'),
        Menu('Command log',
            Menu('this sheet', 'cmdlog-sheet'),
            Menu('this sheet only', 'cmdlog-sheet-only'),
            Menu('all commands', 'cmdlog-all'),
        ),
        Menu('Plugins', 'open-plugins'),
        Menu('Columns',
            Menu('this sheet', 'columns-sheet'),
            Menu('all sheets', 'columns-all'),
        ),
        Menu('Errors',
            Menu('recent', 'error-recent'),
            Menu('all', 'errors-all'),
            Menu('in cell', 'error-cell'),
        ),
        Menu('Search',
            Menu('current column', 'search-col'),
            Menu('visible columns', 'search-cols'),
            Menu('key columns', 'search-keys'),
            Menu('by Python expr', 'search-expr'),
            Menu('again', 'search-next'),
        ),
        Menu('Reverse Search',
            Menu('current column', 'searchr-col'),
            Menu('visible columns', 'searchr-cols'),
            Menu('key columns', 'searchr-keys'),
            Menu('by Python expr', 'searchr-expr'),
            Menu('again', 'searchr-next'),
        ),
        Menu('Split window',
            Menu('in half', 'splitwin-half'),
            Menu('in percent', 'splitwin-input'),
            Menu('unsplit', 'splitwin-close'),
        ),
    ),

    Menu('Column',
        Menu('Hide', 'hide-col'),
        Menu('Type as',
            Menu('No type', 'type-any'),
            Menu('String', 'type-str'),
            Menu('Integer', 'type-int'),
            Menu('Float', 'type-float'),
            Menu('SI Float', 'type-floatsi'),
            Menu('Dirty float', 'type-currency'),
            Menu('Date', 'type-date'),
            Menu('Length', 'type-len'),
        ),
        Menu('Toggle as key', 'key-col'),
        Menu('Sort by',
            Menu('Current column only',
                Menu('Ascending', 'sort-asc'),
                Menu('Descending', 'sort-desc'),
            ),
            Menu('Current column too',
                Menu('Ascending', 'sort-asc-add'),
                Menu('Descending', 'sort-desc-add'),
            ),
            Menu('Key columns',
                Menu('Ascending', 'sort-keys-asc'),
                Menu('Descending', 'sort-keys-desc'),
            ),
        ),
        Menu('Expand', 'expand-col'),
        Menu('Contract', 'contract-col'),
        Menu('Split', 'split-col'),
        Menu('Transform', 'setcol-subst'),
        Menu('Add column',
            Menu('empty', 'addcol-new'),
            Menu('regex capture', 'addcol-capture'),
            Menu('regex transform', 'addcol-subst'),
            Menu('Python expr', 'addcol-expr'),
            Menu('increment', 'addcol-incr'),
            Menu('shell', 'addcol-shell'),
        ),
    ),

    Menu('Select',
        Menu('Current row', 'select-row'),
        Menu('All rows', 'select-rows'),
        Menu('Like current cell', 'select-equal-cell'),
        Menu('Equal to current cell', 'select-exact-cell'),
        Menu('From top', 'select-before'),
        Menu('To bottom', 'select-after'),
        Menu('By Python expr', 'select-expr'),
        Menu('By regex',
            Menu('Current column', 'select-col-regex'),
            Menu('All columns', 'select-cols-regex'),
        ),
        Menu('Errors',
            Menu('Current column', 'select-error-col'),
            Menu('Any column', 'select-error'),
        ),
    ),

    Menu('Tools',
        Menu('Transpose', 'transpose'),
        Menu('Pivot', 'pivot'),
        Menu('Melt', 'melt'),
    ),

    Menu('Help',
        Menu('Quick reference', 'sysopen-help'),
        Menu('Open command list', 'help-commands'),
#        Menu('Tutorial', 'open-tutorial'),
#        Menu('About', 'open-about'),
        Menu('Version', 'show-version'),
    ),
]


@VisiData.api
def getMenuItem(vd):
    try:
        currentItem = vd
        for i in vd.activeMenuItems:
            currentItem = currentItem.menus[i]
    except IndexError:
        vd.activeMenuItems = vd.activeMenuItems[:i-1]

    return currentItem


@VisiData.api
def drawSubmenu(vd, scr, sheet, y, x, menus, level, disp_menu_boxchars=''):
    if not menus:
        return y, x
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_boxchars

    try:
        vd.activeMenuItems[level] %= len(menus)
    except IndexError:
        vd.activeMenuItems = vd.activeMenuItems[:-1]

    w = max(len(item.title) for item in menus)+2

    # draw borders before/under submenus
    if level > 1:
        clipdraw(scr, y-1, x, tl+ts*(w+2)+tr, colors.color_menu)  # top

    clipdraw(scr, y+len(menus), x, bl+bs*(w+2)+br, colors.color_menu) #  bottom

    for i, item in enumerate(menus):
        clipdraw(scr, y+i, x, ls, colors.color_menu)
        if i == vd.activeMenuItems[level]:
            attr = colors.color_menu_active
            if level+1 < len(vd.activeMenuItems):
                vd.drawSubmenu(scr, sheet, y+i, x+w+3, item.menus, level+1, disp_menu_boxchars=disp_menu_boxchars)
        else:
            attr = colors.color_menu

        title = item.title
        pretitle= ' '
        titlenote= ' '
        if item.menus:
            titlenote = vd.options.disp_menu_more
        else:
            cmd = sheet.getCommand(item.longname)
            if cmd and cmd.execstr:
                if 'push(' in cmd.execstr:
                    titlenote = vd.options.disp_menu_push + ' '
                if 'input' in cmd.execstr:
                    title += vd.options.disp_menu_input

        title += ' '*(w-len(pretitle)-len(item.title)+1) # padding

        clipdraw(scr, y+i, x+1, pretitle+title+titlenote, attr)
        clipdraw(scr, y+i, x+3+w, ls, colors.color_menu)

        vd.onMouse(scr, y+i, x, 1, w+3,
                BUTTON1_PRESSED=lambda y,x,key,i=vd.activeMenuItems[:level]+[i]: vd.pressMenu(*i, 0),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)


@VisiData.api
def nop(vd, *args, **kwargs):
    return True


@VisiData.api
def drawMenu(vd, scr, sheet):
    h, w = scr.getmaxyx()
    scr.addstr(0, 0, ' '*(w-1), colors.color_menu)
    clipdraw(scr, 0, w-22, 'Ctrl+H to open menu', colors.color_menu)
    disp_menu_boxchars = sheet.options.disp_menu_boxchars
    x = 1
    ymax = 4
    for i, item in enumerate(vd.menus):
        if vd.activeMenuItems and i == vd.activeMenuItems[0]:
            attr = colors.color_menu_active
            vd.drawSubmenu(scr, sheet, 1, x, item.menus, 1, disp_menu_boxchars)
        else:
            attr = colors.color_menu

        clipdraw(scr, 0, x, ' '+item.title+' ', attr)
        clipdraw(scr, 0, x+1, item.title[0], attr | curses.A_UNDERLINE)
        vd.onMouse(scr, 0, x, 1, len(item.title)+2,
                BUTTON1_PRESSED=lambda y,x,key,i=i: vd.pressMenu(i, 0),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)
        x += len(item.title)+2

    if not vd.activeMenuItems:
        return

    currentItem = vd.getMenuItem()
    cmd = sheet.getCommand(currentItem.longname)

    if not cmd or not cmd.helpstr:
        return

    # help box
    helpw = min(w-4, 76)
    helpx = 2
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_boxchars
    helplines = textwrap.wrap(cmd.helpstr, width=helpw-4)

    menuh = len(vd.menus[vd.activeMenuItems[0]].menus)+2
    y = min(menuh, h-len(helplines)-1)
    clipdraw(scr, y, helpx, tl+ts*(helpw-2)+tr, colors.color_menu)
    for i, line in enumerate(helplines):
        clipdraw(scr, y+i+1, helpx, ls+' '+line+' '*(helpw-len(line)-3)+rs, colors.color_menu)
    clipdraw(scr, y+i+2, helpx, bl+bs*(helpw-2)+br, colors.color_menu)

    mainbinding = HelpSheet().revbinds.get(cmd.longname, [None])[0]
    if mainbinding:
        clipdraw(scr, y, helpx+2, ' '+vd.prettybindkey(mainbinding or '(unbound)')+' ', colors.color_menu_active)
    clipdraw(scr, y, helpx+14, ' '+cmd.longname+' ', colors.color_menu)


@VisiData.api
def prettybindkey(vd, k):
    k = k.replace('^[', 'Alt+')
    k = k[:-1].replace('^', 'Ctrl+')+k[-1]
    if k[-1] in string.ascii_uppercase and '+' not in k and '_' not in k:
        k = k[:-1] + 'Shift+' + k[-1]

    return {
        'Ctrl+I': 'Tab',
        'Ctrl+J': 'Enter',
        ' ': 'Space',
    }.get(k, k).strip()


@VisiData.api
def pressMenu(vd, *args):
    vd.activeMenuItems = list(args)

    if not vd.menuRunning:
        return vd.runMenu()


@VisiData.api
def releaseMenu(vd, *args):
    pass


@VisiData.api
def runMenu(vd):
    old_disp_menu = vd.options.disp_menu

    vd.options.disp_menu=True
    vd.menuRunning = True

    try:
      while True:
        if len(vd.activeMenuItems) < 2:
            vd.activeMenuItems.append(0)

        vd.draw_all()

        k = vd.getkeystroke(vd.scrMenu, vd.activeSheet)

        currentItem = vd.getMenuItem()

        if k in ['^C', '^Q', '^[', 'q']:
            break

        elif k in ['KEY_MOUSE']:
            keystroke, y, x, winname, winscr = vd.parseMouse(menu=vd.scrMenu, top=vd.winTop, bot=vd.winBottom)
            if winname != 'menu':  # clicking off the menu is an escape
                break
            f = vd.getMouse(winscr, x, y, keystroke)
            if f:
                f(y, x, keystroke)
            else:
                break

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

    finally:
        vd.menuRunning = False
        vd.activeMenuItems = []
        vd.options.disp_menu=old_disp_menu


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
BaseSheet.addCommand('^[f', 'menu-file', 'pressMenu(0)', '')
BaseSheet.addCommand('^[e', 'menu-edit', 'pressMenu(1)', '')
BaseSheet.addCommand('^[v', 'menu-view', 'pressMenu(2)', '')
BaseSheet.addCommand('^[c', 'menu-column', 'pressMenu(3)', '')
BaseSheet.addCommand('^[s', 'menu-select', 'pressMenu(4)', '')
BaseSheet.addCommand('^[t', 'menu-tools', 'pressMenu(5)', '')
BaseSheet.addCommand('^[h', 'menu-help', 'pressMenu(6)', '')
BaseSheet.bindkey('^H', 'menu-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'menu-help')
