import string
import textwrap

from visidata import *

__all__ = ['Menu']


vd.option('disp_menu', True, 'show menu on top line when not active')
vd.option('color_menu', 'white on 234 black', 'color of menu items in general')
vd.option('color_menu_active', '223 yellow on black', 'color of active menu submenus/item')
vd.option('color_menu_spec', '118 green on 234 black', 'color of active menu submenus/item')
vd.option('color_menu_help', 'black on 110', 'color of helpbox')
vd.option('disp_menu_boxchars', '││──┌┐└┘', 'box characters to use for menus')
vd.option('disp_menu_more', '»', 'command submenu indicator')
vd.option('disp_menu_push', '⎘', 'indicator if command pushes sheet onto sheet stack')
vd.option('disp_menu_input', '…', 'indicator if input required for command')

BaseSheet.init('activeMenuItems', list)
vd.menuRunning = False


def Menu(title, *args):
    if len(args) == 1 and isinstance(args[0], str):
        return AttrDict(title=title, menus=[], longname=args[0])

    return AttrDict(title=title, menus=list(args), longname='')


def walkmenu(item, menupath=[]):
    if item.menus:
        for i in item.menus:
            yield from walkmenu(i, menupath+[i.title])
    else:
        yield item, menupath


def _finditem(menus, item):
    if isinstance(item, str):
        for m in menus:
            if item == m.title:
                return m
        return None

    return menus[item]


def getMenuItem(obj, menupath=None):
    if menupath is None:
        menupath = obj.activeMenuItems

    try:
        currentItem = obj
        for i in menupath:
            currentItem = _finditem(currentItem.menus, i)
    except IndexError as e:
        vd.exceptionCaught(e)
#        sheet.activeMenuItems = sheet.activeMenuItems[:i-1]

    return currentItem


@VisiData.api
def addMenuItem(vd, *args):
    getMenuItem(vd, args[:-2]).menus.append(Menu(*args[-2:]))


@VisiData.api
def addMenu(vd, *args):
    m = Menu('top', *args)
    for item, menupath in walkmenu(m):
        obj = vd
        for p in menupath:
            c = _finditem(obj.menus, p)
            if not c:
                c = Menu(p)
                obj.menus.append(c)
            obj = c
        obj.longname = item.longname


def _intMenuPath(obj, menupath):
    'Return list of numeric indexes of *menupath* (which may be numeric or string titles) through obj.menus.'
    if not menupath:
        return []

    i = menupath[0]
    if isinstance(i, str):
        try:
            i = [x.title for x in obj.menus].index(i)
        except ValueError:
            vd.warning('no menupath %s' % menupath)
            return

    return [i] + _intMenuPath(obj.menus[i], menupath[1:])


vd.menus = [
    Menu('Sheet',
        Menu('New', 'open-new'),
        Menu('Open file/url', 'open-file'),
        Menu('Rename', 'rename-sheet'),
        Menu('Guard', 'guard-sheet'),
        Menu('Duplicate',
            Menu('selected rows by ref', 'dup-selected'),
            Menu('all rows by ref', 'dup-rows'),
            Menu('selected rows deep', 'dup-selected-deep'),
            Menu('all rows deep', 'dup-rows-deep'),
        ),
        Menu('Freeze', 'freeze-sheet'),
        Menu('Save',
            Menu('current sheet', 'save-sheet'),
            Menu('all sheets', 'save-all'),
            Menu('current column', 'save-col'),
            Menu('keys and current column', 'save-col-keys'),
        ),
        Menu('Commit', 'commit-sheet'),
        Menu('Reload', 'reload-sheet'),
        Menu('Options',
            Menu('All sheets', 'options-global'),
            Menu('This sheet', 'options-sheet'),
            Menu('Edit config file', 'open-config'),
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
        Menu('Modify',
            Menu('current cell',
                Menu('input', 'edit-cell'),
                Menu('Python expression', 'setcell-expr'),
            ),
            Menu('selected cells',
                Menu('from input', 'setcol-input'),
                Menu('from cells above', 'setcol-fill'),
                Menu('increment', 'setcol-incr'),
                Menu('Python sequence', 'setcol-expr'),
                Menu('regex substitution', 'setcol-subst'),
            ),
        ),
        Menu('Slide',
            Menu('Row',
                Menu('up', 'slide-up'),
                Menu('up N', 'slide-up-n'),
                Menu('down', 'slide-down'),
                Menu('down N', 'slide-down-n'),
                Menu('to top', 'slide-top'),
                Menu('to bottom', 'slide-bottom'),
            ),
            Menu('Column',
                Menu('left', 'slide-left'),
                Menu('left N', 'slide-left-n'),
                Menu('leftmost', 'slide-leftmost'),
                Menu('right', 'slide-right'),
                Menu('right N', 'slide-right-n'),
                Menu('rightmost', 'slide-rightmost'),
            ),
        ),
        Menu('Delete',
            Menu('Current row', 'delete-row'),
            Menu('Current cell', 'delete-cell'),
            Menu('Selected rows', 'delete-selected'),
            Menu('Selected cells', 'delete-cells'),
            Menu('Under cursor', 'delete-cursor'),
#            Menu('Visible rows ', 'delete-visible'),
        ),
        Menu('Copy',
            Menu('current row', 'copy-row'),
            Menu('current cell', 'copy-cell'),
            Menu('selected cells', 'copy-cells'),
            Menu('to system clipboard',
                Menu('current cell', 'syscopy-cell'),
                Menu('selected cells', 'syscopy-cells'),
                Menu('current row', 'syscopy-row'),
                Menu('selected rows', 'syscopy-selected'),
            ),
        ),
        Menu('Cut',
            Menu('current row', 'cut-row'),
            Menu('selected cells', 'cut-selected'),
            Menu('current cell', 'cut-cell'),
        ),
        Menu('Paste',
            Menu('row after', 'paste-after'),
            Menu('row before', 'paste-before'),
            Menu('into selected cells', 'setcol-clipboard'),
            Menu('into current cell', 'paste-cell'),
            Menu('from system clipboard',
                Menu('cells at cursor', 'syspaste-cells'),
                Menu('selected cells', 'syspaste-cells-selected'),
            ),
        ),
    ),

    Menu('View',
        Menu('Statuses', 'open-statuses'),
        Menu('Other sheet',
            Menu('previous sheet', 'jump-prev'),
            Menu('first sheet', 'jump-first'),
            Menu('source sheet', 'jump-source'),
        ),
        Menu('Dive into',
            Menu('cursor', 'dive-cursor'),
            Menu('selected cells', 'dive-selected-cells'),
        ),
        Menu('Sheets',
            Menu('stack', 'sheets-stack'),
            Menu('all', 'sheets-all'),
        ),
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
        Menu('Search backward',
            Menu('current column', 'searchr-col'),
            Menu('visible columns', 'searchr-cols'),
            Menu('key columns', 'searchr-keys'),
            Menu('by Python expr', 'searchr-expr'),
            Menu('again', 'searchr-next'),
        ),
        Menu('Split pane',
            Menu('in half', 'splitwin-half'),
            Menu('in percent', 'splitwin-input'),
            Menu('unsplit', 'splitwin-close'),
            Menu('swap panes', 'splitwin-swap-pane'),
            Menu('goto other pane', 'splitwin-swap'),
        ),
        Menu('Refresh screen', 'redraw'),
    ),
    Menu('Column',
        Menu('Hide', 'hide-col'),
        Menu('Unhide all', 'unhide-cols'),
        Menu('Goto',
            Menu('by number', 'go-col-number'),
            Menu('by name', 'go-col-regex'),
        ),
        Menu('Resize',
            Menu('Half', 'resize-col-half'),
            Menu('Max', 'resize-col-max'),
            Menu('All columns max', 'resize-cols-max'),
            Menu('Input', 'resize-col-input'),
        ),
        Menu('Rename',
            Menu('current column', 'rename-col'),
            Menu('from selected cells',
                Menu('current column', 'rename-col-selected'),
                Menu('unnamed columns', 'rename-cols-row'),
                Menu('all columns', 'rename-cols-selected'),
            ),
        ),
        Menu('Type as',
            Menu('No type', 'type-any'),
            Menu('String', 'type-string'),
            Menu('Integer', 'type-int'),
            Menu('Float', 'type-float'),
            Menu('SI Float', 'type-floatsi'),
            Menu('Locale float', 'type-floatlocale'),
            Menu('Dirty float', 'type-currency'),
            Menu('Date', 'type-date'),
            Menu('Custom date format', 'type-customdate'),
            Menu('Length', 'type-len'),
        ),
        Menu('Key',
            Menu('Toggle current column', 'key-col'),
            Menu('Unkey current column', 'key-col-off'),
        ),
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
        Menu('Expand',
            Menu('one level', 'expand-col'),
            Menu('to depth', 'expand-col-depth'),
            Menu('all columns one level', 'expand-cols'),
            Menu('all columns to depth', 'expand-cols-depth'),
        ),
        Menu('Contract', 'contract-col'),
        Menu('Split', 'split-col'),
        Menu('Aggregate', 'aggregate-col'),
        Menu('Fill', 'setcol-fill'),
        Menu('Freeze', 'freeze-col'),
        Menu('Add column',
            Menu('empty',
                Menu('one column', 'addcol-new'),
                Menu('columns', 'addcol-bulk'),
            ),
            Menu('regex capture', 'addcol-capture'),
            Menu('regex transform', 'addcol-subst'),
            Menu('Python expr', 'addcol-expr'),
            Menu('increment', 'addcol-incr'),
            Menu('shell', 'addcol-shell'),
        ),
    ),

    Menu('Row',
        Menu('Dive into', 'open-row'),
        Menu('Goto',
            Menu('top', 'go-top'),
            Menu('bottom', 'go-bottom'),
            Menu('previous',
                Menu('page', 'go-pageup'),
                Menu('null', 'go-prev-null'),
                Menu('value', 'go-prev-value'),
            ),
            Menu('next',
                Menu('page', 'go-pagedown'),
                Menu('null', 'go-next-null'),
                Menu('value', 'go-next-value'),
            ),
        ),
        Menu('Select',
            Menu('Current row', 'select-row'),
            Menu('All rows', 'select-rows'),
            Menu('From top', 'select-before'),
            Menu('To bottom', 'select-after'),
            Menu('By Python expr', 'select-expr'),
            Menu('By regex',
                Menu('Current column', 'select-col-regex'),
                Menu('All columns', 'select-cols-regex'),
            ),
            Menu('Equal to current cell', 'select-equal-cell'),
            Menu('Equal to current row', 'select-equal-row'),
            Menu('Errors',
                Menu('Current column', 'select-error-col'),
                Menu('Any column', 'select-error'),
            ),
        ),
        Menu('Unselect',
            Menu('Current row', 'unselect-row'),
            Menu('All rows', 'unselect-rows'),
            Menu('From top', 'unselect-before'),
            Menu('To bottom', 'unselect-after'),
            Menu('By Python expr', 'unselect-expr'),
            Menu('By regex',
                Menu('Current column', 'unselect-col-regex'),
                Menu('All columns', 'unselect-cols-regex'),
            ),
        ),
        Menu('Toggle select',
            Menu('Current row', 'stoggle-row'),
            Menu('All rows', 'stoggle-rows'),
            Menu('From top', 'stoggle-before'),
            Menu('To bottom', 'stoggle-after'),
        ),
    ),

    Menu('Data',
        Menu('Transpose', 'transpose'),
        Menu('Frequency table',
            Menu('current column', 'freq-col'),
            Menu('key columns', 'freq-keys'),
        ),
        Menu('Statistics', 'describe-sheet'),
        Menu('Pivot', 'pivot'),
        Menu('Unfurl column', 'unfurl-col'),
        Menu('Melt',
            Menu('nonkey columns', 'melt'),
            Menu('nonkey columns by regex', 'melt-regex'),
        ),
        Menu('Join',
            Menu('top two sheets', 'join-sheets-top2'),
            Menu('all sheets', 'join-sheets-all'),
        ),
    ),

    Menu('Plot',
        Menu('Graph',
            Menu('current column', 'plot-column'),
            Menu('all numeric columns', 'plot-numerics'),
        ),
        Menu('Resize cursor',
            Menu('height',
                Menu('double', 'resize-cursor-doubleheight'),
                Menu('half','resize-cursor-halfheight'),
                Menu('shorter','resize-cursor-shorter'),
                Menu('taller','resize-cursor-taller'),
            ),
            Menu('width',
                Menu('double', 'resize-cursor-doublewide'),
                Menu('half','resize-cursor-halfwide'),
                Menu('thinner','resize-cursor-thinner'),
                Menu('wider','resize-cursor-wider'),
            ),
        ),
        Menu('Resize graph',
            Menu('X axis', 'resize-x-input'),
            Menu('Y axis', 'resize-y-input'),
            Menu('aspect ratio', 'set-aspect'),
        ),
        Menu('Zoom',
            Menu('out', 'zoomout-cursor'),
            Menu('in', 'zoomin-cursor'),
            Menu('cursor', 'zoom-all'),
        ),
    ),
    Menu('Meta',
        Menu('Macros sheet', 'macro-sheet'),
        Menu('Threads sheet', 'threads-all'),
        Menu('Import Python library', 'import-python'),
        Menu('Exec Python statement', 'exec-python'),
        Menu('Execute VisiData longname', 'exec-longname'),
        Menu('Toggle profiling', 'toggle-profile'),
        Menu('Suspend to shell', 'suspend'),
        Menu('Open as Python Object',
            Menu('Sheet', 'pyobj-sheet'),
            Menu('Row', 'pyobj-row'),
            Menu('Cell', 'pyobj-cell'),
            Menu('Python expression', 'pyobj-expr'),
        ),
    ),
]

vd.addMenu(Menu('Help',
        Menu('Quick reference', 'sysopen-help'),
        Menu('Open command list', 'help-commands'),
#        Menu('Tutorial', 'open-tutorial'),
#        Menu('About', 'open-about'),
        Menu('Version', 'show-version'),
    ))


@BaseSheet.api
def menuitemAvailable(sheet, item):
    return any(sheet.menuitemAvailable(i) for i in item.menus)


@VisiData.api
def drawSubmenu(vd, scr, sheet, y, x, menus, level, disp_menu_boxchars=''):
    if not menus:
        return
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_boxchars

    try:
        sheet.activeMenuItems[level] %= len(menus)
    except IndexError:
        pass # sheet.activeMenuItems = sheet.activeMenuItems[:-1]

    w = max(len(item.title) for item in menus)+1

    # draw borders before/under submenus
    if level > 1:
        clipdraw(scr, y-1, x, tl+ts*(w+2)+tr, colors.color_menu)  # top

    clipdraw(scr, y+len(menus), x, bl+bs*(w+2)+br, colors.color_menu) #  bottom

    i = 0
    for j, item in enumerate(menus):
        attr = colors.color_menu

        if any(x.obj not in ['BaseSheet', 'TableSheet'] for x, _ in walkmenu(item)):
            attr = colors.color_menu_spec

        if level < len(sheet.activeMenuItems):
          if j == sheet.activeMenuItems[level]:
            attr = colors.color_menu_active

            if level < len(sheet.activeMenuItems):
                vd.drawSubmenu(scr, sheet, y+i, x+w+3, item.menus, level+1, disp_menu_boxchars=disp_menu_boxchars)

        clipdraw(scr, y+i, x, ls, colors.color_menu)

        title = item.title
        pretitle= ' '
        titlenote= ' '
        if item.menus:
            titlenote = vd.options.disp_menu_more

        # special notes
        if item.cmd:
            if item.cmd.execstr:
                if 'push(' in item.cmd.execstr:
                    titlenote = vd.options.disp_menu_push + ' '
                if 'input' in item.cmd.execstr:
                    title += vd.options.disp_menu_input

        # actually display the menu item
        title += ' '*(w-len(pretitle)-len(item.title)+1) # padding

        clipdraw(scr, y+i, x+1, pretitle+title+titlenote, attr)
        clipdraw(scr, y+i, x+3+w, ls, colors.color_menu)

        vd.onMouse(scr, y+i, x, 1, w+3,
                BUTTON1_PRESSED=lambda y,x,key,i=sheet.activeMenuItems[:level]+[j]: sheet.pressMenu(*i, 0),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)

        i += 1


@VisiData.api
def nop(vd, *args, **kwargs):
    return True


@BaseSheet.property
@drawcache
def menus(sheet):
    'List of Hierarchical menu items for commands available on this sheet.'
    def _menus(sheet, item):
        if item.longname:
            cmd = sheet.getCommand(item.longname)
            if cmd:
                item.cmd = cmd
                if vd.commands[item.longname].get('TableSheet', None):
                    item.obj = 'TableSheet'
                elif vd.commands[item.longname].get('BaseSheet', None):
                    item.obj = 'BaseSheet'
                else:
                    item.obj = ''
                return item

        elif item.menus:
            menus = _menu_list(sheet, item.menus)
            if menus:
                title = getattr(item, 'title', '')
                return AttrDict(title=title, menus=menus, longname='')
        else:
            return item

    def _menu_list(sheet, menus):
        ret = []
        for i in menus:
            m = _menus(sheet, i)
            if m:
                ret.append(m)
        return ret

    return _menu_list(sheet, vd.menus)


@VisiData.api
def drawMenu(vd, scr, sheet):
    h, w = scr.getmaxyx()
    scr.addstr(0, 0, ' '*(w-1), colors.color_menu)
    disp_menu_boxchars = sheet.options.disp_menu_boxchars
    x = 1
    ymax = 4
    toplevel = sheet.menus
    for i, item in enumerate(toplevel):
        if sheet.activeMenuItems and i == sheet.activeMenuItems[0]:
            attr = colors.color_menu_active
            vd.drawSubmenu(scr, sheet, 1, x, item.menus, 1, disp_menu_boxchars)
        else:
            attr = colors.color_menu

        clipdraw(scr, 0, x, ' '+item.title+' ', attr)
        clipdraw(scr, 0, x+1, item.title[0], attr | curses.A_UNDERLINE)
        vd.onMouse(scr, 0, x, 1, len(item.title)+2,
                BUTTON1_PRESSED=lambda y,x,key,i=i,sheet=sheet: sheet.pressMenu(i, 0),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)
        x += len(item.title)+2


    rightdisp = 'Ctrl+H for menu'
    rightmenux = min(72, w-len(rightdisp))
    if rightmenux > x:
        clipdraw(scr, 0, rightmenux, rightdisp, colors.color_menu)

    if not sheet.activeMenuItems:
        return

    currentItem = getMenuItem(sheet)
    cmd = currentItem.cmd

    if not cmd:
        return

    # help box
    helpattr = colors.color_menu_help
    helpw = min(w-4, 76)
    helpx = 2
    ls,rs,ts,bs,tl,tr,bl,br = disp_menu_boxchars
    helplines = textwrap.wrap(cmd.helpstr or '(no help available)', width=helpw-4)

    menuh = len(toplevel[sheet.activeMenuItems[0]].menus)+2
    y = min(menuh, h-len(helplines)-1)
    clipdraw(scr, y, helpx, tl+ts*(helpw-2)+tr, helpattr)
    for i, line in enumerate(helplines):
        clipdraw(scr, y+i+1, helpx, ls+' '+line+' '*(helpw-len(line)-3)+rs, helpattr)
    clipdraw(scr, y+i+2, helpx, bl+bs*(helpw-2)+br, helpattr)

    mainbinding = HelpSheet().revbinds.get(cmd.longname, [None])[0]
    if mainbinding:
        clipdraw(scr, y, helpx+2, ' '+vd.prettybindkey(mainbinding or '(unbound)')+' ', colors.color_menu_active)
    clipdraw(scr, y, helpx+14, ' '+cmd.longname+' ', helpattr)


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


@BaseSheet.api
def pressMenu(sheet, *args):
    def _findMenu(i):
        if isinstance(i, str):
            i = [x.title for x in sheet.menus].index(i)
        return i

    sheet.activeMenuItems = _intMenuPath(sheet, args)

    if not vd.menuRunning:
        return vd.runMenu()


@VisiData.api
def runMenu(vd):
    old_disp_menu = vd.options.disp_menu

    vd.options.disp_menu=True
    vd.menuRunning = True
    sheet = vd.activeSheet

    try:
      while True:
        if len(sheet.activeMenuItems) < 2:
            sheet.activeMenuItems.append(0)

        vd.draw_all()

        k = vd.getkeystroke(vd.scrMenu, sheet)

        currentItem = getMenuItem(sheet)

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
                sheet.activeMenuItems.append(0)
            else:
                sheet.activeMenuItems = [sheet.activeMenuItems[0]+1, 0]

        elif k in ['KEY_LEFT', 'h']:
            if len(sheet.activeMenuItems) > 2:
                sheet.activeMenuItems.pop(-1)
            else:
                sheet.activeMenuItems = [sheet.activeMenuItems[0]-1, 0]

        elif k in ['KEY_DOWN', 'j']:
            sheet.activeMenuItems[-1] += 1

        elif k in ['KEY_UP', 'k']:
            sheet.activeMenuItems[-1] -= 1

        elif k in [ENTER, ' ']:
            if currentItem.menus:
                sheet.activeMenuItems.append(0)
            else:
                # undo menu and redraw all so input is visible
                vd.menuRunning = False
                sheet.activeMenuItems = []
                vd.options.disp_menu=old_disp_menu
                vd.draw_all()
                sheet.execCommand(currentItem.longname)
                break

        sheet.checkMenu()

    finally:
        vd.menuRunning = False
        sheet.activeMenuItems = []
        vd.options.disp_menu=old_disp_menu


@BaseSheet.api
def checkMenu(sheet):
    sheet.activeMenuItems[0] %= len(sheet.menus)


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

BaseSheet.addCommand('^[s', 'menu-sheet', 'pressMenu("Sheet")', '')
BaseSheet.addCommand('^[e', 'menu-edit', 'pressMenu("Edit")', '')
BaseSheet.addCommand('^[v', 'menu-view', 'pressMenu("View")', '')
BaseSheet.addCommand('^[c', 'menu-column', 'pressMenu("Column")', '')
BaseSheet.addCommand('^[r', 'menu-row', 'pressMenu("Row")', '')
BaseSheet.addCommand('^[d', 'menu-data', 'pressMenu("Data")', '')
BaseSheet.addCommand('^[p', 'menu-plot', 'pressMenu("Plot")', '')
BaseSheet.addCommand('^[m', 'menu-meta', 'pressMenu("Meta")', '')
BaseSheet.addCommand('^[h', 'menu-help', 'pressMenu("Help")', '')
BaseSheet.bindkey('^H', 'menu-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'menu-help')
