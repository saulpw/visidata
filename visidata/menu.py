import string
import textwrap

from visidata import *


vd.option('disp_menu', True, 'show menu on top line when not active', sheettype=None)
vd.option('disp_menu_keys', True, 'show keystrokes inline in submenus', sheettype=None)
vd.option('color_menu', 'black on 110 cyan', 'color of menu items in general')
vd.option('color_menu_active', '223 yellow on black', 'color of active menu items')
vd.option('color_menu_spec', 'black on 34 green', 'color of sheet-specific menu items')
vd.option('color_menu_help', 'black italic on 110 cyan', 'color of helpbox')

vd.option('disp_menu_boxchars', '││──┌┐└┘├┤', 'box characters to use for menus')
vd.option('disp_menu_more', '»', 'command submenu indicator')
vd.option('disp_menu_push', '⎘', 'indicator if command pushes sheet onto sheet stack')
vd.option('disp_menu_input', '…', 'indicator if input required for command')
vd.option('disp_menu_fmt', 'Ctrl+H for help menu', 'right-side menu format string')

BaseSheet.init('activeMenuItems', list)
vd.menuRunning = False

def menudraw(*args):
    return clipdraw(*args, truncator=' ')


def Menu(title, *args):
    'Construct menu command or submenu.  *title* is displayed text for this item; *args* is either a single command longname, or recursive Menu elements.'
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
    'Add one command to hierarchical menu at given menupath.  Last argument must be valid command longname. Append menupath elements that do not exist. Example: vd.addMenuItem("File", "Options", "more options", "options-more")'
    m = Menu(*args[-2:])
    for x in reversed(args[:-2]):
        m = Menu(x, m)
    vd.addMenu(m)


@VisiData.api
def addMenu(vd, *args):
    '''Incorporate submenus and commands into hierarchical menu.  Wrap all in Menu() objects.  Example:

        vd.addMenu(Menu("Help",
                    Menu("About",
                      Menu("credits", "show-credits"),
                      Menu("environment", "show-env"),
                  )))'''
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
            return []

    return [i] + _intMenuPath(obj.menus[i], menupath[1:])


vd.menus = [
    Menu('File',
        Menu('New', 'open-new'),
        Menu('Open file/url', 'open-file'),
        Menu('Rename', 'rename-sheet'),
        Menu('Guard', 
            Menu('on', 'guard-sheet'),
            Menu('off', 'guard-sheet-off')
        ),
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
            Menu('all sheets', 'options-global'),
            Menu('this sheet', 'options-sheet'),
            Menu('edit config file', 'open-config'),
        ),
        Menu('Quit',
            Menu('top sheet', 'quit-sheet'),
            Menu('all sheets', 'quit-all'),
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
            Menu('current row', 'delete-row'),
            Menu('current cell', 'delete-cell'),
            Menu('selected rows', 'delete-selected'),
            Menu('selected cells', 'delete-cells'),
            Menu('under cursor', 'delete-cursor'),
#            Menu('Visible rows ', 'delete-visible'),
        ),
        Menu('Copy',
            Menu('current cell', 'copy-cell'),
            Menu('current row', 'copy-row'),
            Menu('selected cells', 'copy-cells'),
            Menu('selected rows', 'copy-selected'),
            Menu('to system clipboard',
                Menu('current cell', 'syscopy-cell'),
                Menu('current row', 'syscopy-row'),
                Menu('selected cells', 'syscopy-cells'),
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
        Menu('Plugins', 'open-plugins'),
        Menu('Other sheet',
            Menu('previous sheet', 'jump-prev'),
            Menu('first sheet', 'jump-first'),
            Menu('source sheet', 'jump-source'),
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
        Menu('Visibility',
            Menu('Methods and dunder attributes',
                Menu('show', 'show-hidden'),
                Menu('hide', 'hide-hidden'),
            ),
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
            Menu('half', 'resize-col-half'),
            Menu('current column to max', 'resize-col-max'),
            Menu('current column to input', 'resize-col-input'),
            Menu('all columns max', 'resize-cols-max'),
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
            Menu('anytype', 'type-any'),
            Menu('string', 'type-string'),
            Menu('integer', 'type-int'),
            Menu('float', 'type-float'),
            Menu('SI float', 'type-floatsi'),
            Menu('locale float', 'type-floatlocale'),
            Menu('dirty float', 'type-currency'),
            Menu('date', 'type-date'),
            Menu('custom date format', 'type-customdate'),
            Menu('length', 'type-len'),
        ),
        Menu('Key',
            Menu('toggle current column', 'key-col'),
            Menu('unkey current column', 'key-col-off'),
        ),
        Menu('Sort by',
            Menu('current column only',
                Menu('ascending', 'sort-asc'),
                Menu('descending', 'sort-desc'),
            ),
            Menu('current column too',
                Menu('ascending', 'sort-asc-add'),
                Menu('descending', 'sort-desc-add'),
            ),
            Menu('key columns',
                Menu('ascending', 'sort-keys-asc'),
                Menu('descending', 'sort-keys-desc'),
            ),
        ),
        Menu('Add column',
            Menu('empty',
                Menu('one column', 'addcol-new'),
                Menu('columns', 'addcol-bulk'),
            ),
            Menu('capture by regex', 'addcol-capture'),
            Menu('split by regex', 'addcol-split'),
            Menu('subst by regex', 'addcol-subst'),
            Menu('Python expr', 'addcol-expr'),
            Menu('increment', 'addcol-incr'),
            Menu('shell', 'addcol-shell'),
        ),
        Menu('Expand',
            Menu('one level', 'expand-col'),
            Menu('to depth', 'expand-col-depth'),
            Menu('all columns one level', 'expand-cols'),
            Menu('all columns to depth', 'expand-cols-depth'),
        ),
        Menu('Contract', 'contract-col'),
        Menu('Split', 'split-col'),
        Menu('Add aggregator', 'aggregate-col'),
        Menu('Fill', 'setcol-fill'),
        Menu('Freeze', 'freeze-col'),
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
                Menu('selected', 'go-prev-selected'),
            ),
            Menu('next',
                Menu('page', 'go-pagedown'),
                Menu('null', 'go-next-null'),
                Menu('value', 'go-next-value'),
                Menu('selected', 'go-next-selected'),
            ),
        ),
        Menu('Select',
            Menu('current row', 'select-row'),
            Menu('all rows', 'select-rows'),
            Menu('from top', 'select-before'),
            Menu('to bottom', 'select-after'),
            Menu('by Python expr', 'select-expr'),
            Menu('by regex',
                Menu('current column', 'select-col-regex'),
                Menu('all columns', 'select-cols-regex'),
            ),
            Menu('equal to current cell', 'select-equal-cell'),
            Menu('equal to current row', 'select-equal-row'),
            Menu('errors',
                Menu('current column', 'select-error-col'),
                Menu('any column', 'select-error'),
            ),
        ),
        Menu('Unselect',
            Menu('current row', 'unselect-row'),
            Menu('all rows', 'unselect-rows'),
            Menu('from top', 'unselect-before'),
            Menu('to bottom', 'unselect-after'),
            Menu('by Python expr', 'unselect-expr'),
            Menu('by regex',
                Menu('current column', 'unselect-col-regex'),
                Menu('all columns', 'unselect-cols-regex'),
            ),
        ),
        Menu('Toggle select',
            Menu('current row', 'stoggle-row'),
            Menu('all rows', 'stoggle-rows'),
            Menu('from top', 'stoggle-before'),
            Menu('to bottom', 'stoggle-after'),
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
        Menu('Dive into cursor', 'dive-cursor'),
    ),
    Menu('System',
        Menu('Macros sheet', 'macro-sheet'),
        Menu('Threads sheet', 'threads-all'),
        Menu('Execute longname', 'exec-longname'),
        Menu('Python',
            Menu('import library', 'import-python'),
            Menu('current sheet', 'pyobj-sheet'),
            Menu('current row', 'pyobj-row'),
            Menu('current cell', 'pyobj-cell'),
            Menu('expression', 'pyobj-expr'),
            Menu('exec()', 'exec-python'),
        ),
        Menu('Toggle profiling', 'toggle-profile'),
        Menu('Suspend to shell', 'suspend'),
    ),
]

vd.addMenu(Menu('Help',
        Menu('Quick reference', 'sysopen-help'),
        Menu('Command list', 'help-commands'),
        Menu('Version', 'show-version'),
    ))


@BaseSheet.api
def menuitemAvailable(sheet, item):
    return any(sheet.menuitemAvailable(i) for i in item.menus)


@VisiData.api
def drawSubmenu(vd, scr, sheet, y, x, menus, level, disp_menu_boxchars=''):
    if not menus:
        return
    ls,rs,ts,bs,tl,tr,bl,br,lsr,rsl = disp_menu_boxchars

    try:
        sheet.activeMenuItems[level] %= len(menus)
    except IndexError:
        pass # sheet.activeMenuItems = sheet.activeMenuItems[:-1]

    for item in menus:
        if item.cmd:
            mainbinding = sheet.revbinds.get(item.cmd.longname, [None])[0]
            item.binding = vd.prettykeys(mainbinding)

    maxbinding = 0
    if vd.options.disp_menu_keys:
        maxbinding = max(len(item.binding or '') for item in menus)+2

    w = max(len(item.title) for item in menus)+maxbinding+2

    # draw borders before/under submenus
    if level > 1:
        menudraw(scr, y-1, x, tl+ts*(w+2)+tr, colors.color_menu)  # top

    menudraw(scr, y+len(menus), x, bl+bs*(w+2)+br, colors.color_menu) #  bottom

    i = 0
    for j, item in enumerate(menus):
        attr = colors.color_menu
        bindattr = colors.color_keystrokes

        if any(foo.obj not in ['BaseSheet', 'TableSheet'] for foo, _ in walkmenu(item)):
            bindattr = attr = colors.color_menu_spec

        if level < len(sheet.activeMenuItems):
          if j == sheet.activeMenuItems[level]:
            bindattr = attr = colors.color_menu_active

            if level < len(sheet.activeMenuItems):
                vd.drawSubmenu(scr, sheet, y+i, x+w+4, item.menus, level+1, disp_menu_boxchars=disp_menu_boxchars)

        menudraw(scr, y+i, x, ls, colors.color_menu)

        title = item.title
        pretitle= ' '
        titlenote= ' '
        if item.menus:
            titlenote = vd.options.disp_menu_more

        mainbinding = ' '*maxbinding
        # special notes
        if item.cmd:
            if item.cmd.execstr:
                if 'push(' in item.cmd.execstr:
                    titlenote = vd.options.disp_menu_push + ' '
                if 'input' in item.cmd.execstr:
                    title += vd.options.disp_menu_input

                if maxbinding:
                    revbinds = sheet.revbinds.get(item.cmd.longname, [])
                    if revbinds:
                        mainbinding = vd.prettykeys(revbinds[0])
                        mainbinding += ' '*(maxbinding-len(mainbinding))

        # actually display the menu item
        title += ' '*(w-len(pretitle)-len(item.title)-maxbinding+1) # padding

        menudraw(scr, y+i, x+1, pretitle+title, attr)
        if maxbinding:
            menudraw(scr, y+i, x+1+w-maxbinding, '  ' + mainbinding, bindattr)
        menudraw(scr, y+i, x+2+w, titlenote, attr)
        menudraw(scr, y+i, x+3+w, ls, colors.color_menu)

        vd.onMouse(scr, y+i, x, 1, w+3,
                BUTTON1_PRESSED=lambda y,x,key,p=sheet.activeMenuItems[:level]+[j]: sheet.pressMenu(*p),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_CLICKED=lambda y,x,key,p=sheet.activeMenuItems[:level]+[j]: sheet.pressMenu(*p),
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)

        i += 1


@VisiData.api
def nop(vd, *args, **kwargs):
    return False


@BaseSheet.property
@drawcache
def menus(sheet):
    'List of hierarchical menu items for commands available on this sheet.'
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

        menudraw(scr, 0, x, ' ', attr)
        for j, ch in enumerate(item.title):
            menudraw(scr, 0, x+j+1, ch, attr | (curses.A_UNDERLINE if ch.isupper() else 0))
        menudraw(scr, 0, x+j+2, ' ', attr)

        vd.onMouse(scr, 0, x, 1, len(item.title)+2,
                BUTTON1_PRESSED=lambda y,x,key,i=i,sheet=sheet: sheet.pressMenu(i),
                BUTTON2_PRESSED=vd.nop,
                BUTTON3_PRESSED=vd.nop,
                BUTTON1_CLICKED=lambda y,x,key,i=i,sheet=sheet: sheet.pressMenu(i),
                BUTTON1_RELEASED=vd.nop,
                BUTTON2_RELEASED=vd.nop,
                BUTTON3_RELEASED=vd.nop)
        x += len(item.title)+2


    rightdisp = sheet.options.disp_menu_fmt.format(sheet=sheet, vd=vd)
    menudraw(scr, 0, x+4, rightdisp, colors.color_menu)

    if not sheet.activeMenuItems:
        return

    currentItem = getMenuItem(sheet)
    cmd = currentItem.cmd

    if not cmd:
        return

    # helpbox
    sidelines = []
    if 'push(' in cmd.execstr:
        sidelines += [vd.options.disp_menu_push + ' pushes sheet']
    if 'input' in cmd.execstr:
        sidelines += [vd.options.disp_menu_input + ' needs input']

    helpattr = colors.color_menu_help
    helpx = 30
    helpw = min(w-helpx-4, 76)
    ls,rs,ts,bs,tl,tr,bl,br,lsr,rsl = disp_menu_boxchars
    helplines = textwrap.wrap(cmd.helpstr or '(no help available)', width=helpw-4)

    # place helpbox just below deepest menu
    menuh = 2+sum(sheet.activeMenuItems[1:-1])
    menuh += len(getMenuItem(sheet, sheet.activeMenuItems[:-1]).menus)
    menuy = 16 # min(menuh, h-len(helplines)-3)

    y = menuy
    menudraw(scr, y, helpx, tl+ts*(helpw-2)+tr, helpattr) # top line
    y += 1

    # cmd.helpstr text
    for i, line in enumerate(helplines):
        menudraw(scr, y+i, helpx, ls+' '+line+' '*(helpw-len(line)-3)+rs, helpattr)
    y += len(helplines)

    if sidelines:
        menudraw(scr, y, helpx, ls+' '*(helpw-2)+rs, helpattr)
        for i, line in enumerate(sidelines):
            menudraw(scr, y+i+1, helpx, ls+'    '+line+' '*(helpw-len(line)-6)+rs, helpattr)
        y += len(sidelines)+1

    menudraw(scr, y, helpx, bl+bs*(helpw-2)+br, helpattr)

    mainbinding = sheet.revbinds.get(cmd.longname, [None])[0]
    if mainbinding:
        menudraw(scr, menuy, helpx+2, rsl, helpattr)
        ks = vd.prettykeys(mainbinding or '(unbound)')
        menudraw(scr, menuy, helpx+3, ' '+ks+' ', colors.color_menu_active)
        menudraw(scr, menuy, helpx+2+len(ks)+3, lsr, helpattr)
    menudraw(scr, menuy, helpx+19, ' '+cmd.longname+' ', helpattr)


@BaseSheet.api
def pressMenu(sheet, *args):
    '''Navigate to given menupath in *args* and activate menu if not already activated. Return True if pressing current item.
    Example: sheet.pressMenu("Help", "Version")
    '''
    ret = False
    p = _intMenuPath(sheet, args)
    if p == sheet.activeMenuItems:  # clicking on current menu item
        if getMenuItem(sheet, p).longname:
            ret = True
        else:
            p += [0]

    sheet.activeMenuItems = p

    if not vd.menuRunning:
        vd.runMenu()

    return ret


@BaseSheet.api
def checkMenu(sheet):
    sheet.activeMenuItems[0] %= len(sheet.menus)


@VisiData.api
def runMenu(vd):
    'Activate menu, with sheet.activeMenuItems containing the navigated menu path.  Does not return until menu is deactivated.'
    old_disp_menu = vd.options.disp_menu

    vd.options.disp_menu=True
    vd.menuRunning = True
    sheet = vd.activeSheet
    vd.setWindows(vd.scrFull)
    nEscapes = 0

    try:
      while True:
        if len(sheet.activeMenuItems) < 2:
            sheet.activeMenuItems.append(0)

        vd.draw_all()

        k = vd.getkeystroke(vd.scrMenu, sheet)

        currentItem = getMenuItem(sheet)

        if k == '^[':  # ESC
            nEscapes += 1  #1470
        else:
            nEscapes = 0

        if nEscapes > 1 or k in ['^C', '^Q', 'q']:
            return

        elif k in ['KEY_MOUSE']:
            keystroke, y, x, winname, winscr = vd.parseMouse(menu=vd.scrMenu, top=vd.winTop, bot=vd.winBottom)
            if winname != 'menu':  # clicking off the menu is an escape
                return
            f = vd.getMouse(winscr, x, y, keystroke)
            if f:
                if f(y, x, keystroke):
                    break
            else:
                return

        elif k in ['KEY_RIGHT', 'l']:
            if currentItem.menus and sheet.activeMenuItems[1] != 0:  # not first item
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

        elif k in [ENTER, ' ', '^J', '^M']:
            if currentItem.menus:
                sheet.activeMenuItems.append(0)
            else:
                break

        elif k in main_menu.keys():
            sheet.pressMenu(main_menu[k])


        sheet.checkMenu()

    finally:
        vd.menuRunning = False
        sheet.activeMenuItems = []
        vd.options.disp_menu=old_disp_menu

    vd.draw_all()
    sheet.execCommand(currentItem.longname)

main_menu = {'f': 'File', 'e': 'Edit', 'v': 'View', 'c': 'Column', 'r': 'Row', 'd': 'Data', 'p': 'Plot', 's': 'System', 'h': 'Help'}

BaseSheet.addCommand('^[f', 'menu-file', 'pressMenu("File")', '')
BaseSheet.addCommand('^[e', 'menu-edit', 'pressMenu("Edit")', '')
BaseSheet.addCommand('^[v', 'menu-view', 'pressMenu("View")', '')
BaseSheet.addCommand('^[c', 'menu-column', 'pressMenu("Column")', '')
BaseSheet.addCommand('^[r', 'menu-row', 'pressMenu("Row")', '')
BaseSheet.addCommand('^[d', 'menu-data', 'pressMenu("Data")', '')
BaseSheet.addCommand('^[p', 'menu-plot', 'pressMenu("Plot")', '')
BaseSheet.addCommand('^[s', 'menu-system', 'pressMenu("System")', '')
BaseSheet.addCommand('^[h', 'menu-help', 'pressMenu("Help")', '')
BaseSheet.bindkey('^H', 'menu-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'menu-help')

vd.addGlobals({'Menu': Menu})
