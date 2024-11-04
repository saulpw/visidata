import string
import textwrap
import time
import curses

from typing import List, Union
from visidata import vd, drawcache, colors, clipdraw, dispwidth
from visidata import BaseSheet, VisiData, AttrDict, ENTER

vd.option('disp_menu', True, 'show menu on top line when not active', sheettype=None)
vd.theme_option('disp_menu_keys', True, 'show keystrokes inline in submenus', sheettype=None)
vd.theme_option('color_menu', 'black on 68 blue', 'color of menu items in general')
vd.theme_option('color_menu_active', '223 yellow on black', 'color of active menu items')
vd.theme_option('color_menu_spec', 'black on 34 green', 'color of sheet-specific menu items')
vd.theme_option('color_menu_help', 'black italic on 68 blue', 'color of helpbox')

vd.theme_option('disp_menu_boxchars', '││──┌┐└┘├┤', 'box characters to use for menus')
vd.theme_option('disp_menu_more', '»', 'command submenu indicator')
vd.theme_option('disp_menu_push', '⎘', 'indicator if command pushes sheet onto sheet stack')
vd.theme_option('disp_menu_input', '…', 'indicator if input required for command')
vd.option('disp_menu_fmt', '| VisiData {vd.version} | {vd.hintStatus}', 'right-side menu format string')

BaseSheet.init('activeMenuItems', list)
vd.menuRunning = False

@VisiData.property
def hintStatus(vd):
    if vd.options.disp_expert <= 0:
        if int(time.time()/60) % 2 == 0:
            return 'Alt+H for help menu'
        else:
            return 'Ctrl+G to cycle help sidebar'

    return vd.sheet.getHint()

def menudraw(*args):
    return clipdraw(*args, truncator='')


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


def _finditem(menus, item:Union[str,int]):
    if isinstance(item, str):
        for m in menus:
            if item == m.title:
                return m
        return None

    return menus[item]


@BaseSheet.api
def getMenuItem(sheet, menupath:List[str]=None):
    if not menupath:
        menupath = sheet.activeMenuItems

    try:
        currentItem = sheet
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
def addMenuItems(vd, *itemgroups):
    '''Add any number of commands to menu, separated by lines, with individual menupaths separated by '>' character.  Example:
        vd.addMenuItems("""
            Help > About > credits > show-credits
            Help > About > environment > show-env
        """)
    '''
    for itemgroup in itemgroups:
        for itemline in itemgroup.splitlines():
            if not itemline: continue
            menupath = [x.strip() for x in itemline.split('>')]
            vd.addMenuItem(*menupath)


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
        assert not obj.menus, 'cannot override submenu with longname'
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

vd.menus = []

vd.addMenu(
    Menu('File'),
    Menu('Edit'),
    Menu('View'),
    Menu('Column'),
    Menu('Row'),
    Menu('Data'),
    Menu('Plot'),
    Menu('System'),
    Menu('Help')
)


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
        maxbinding = max(len(item.binding or '') for item in menus)+1

    w = max(len(item.title) for item in menus)+maxbinding+2

    # draw borders before/under submenus
    if level > 1:
        menudraw(scr, y-1, x, tl+ts*(w+2)+tr, colors.color_menu)  # top

    menudraw(scr, y+len(menus), x, bl+bs*(w+2)+br, colors.color_menu) #  bottom

    i = 0
    for j, item in enumerate(menus):
        attr = colors.color_menu

        if any(foo.obj not in ['BaseSheet', 'TableSheet'] for foo, _ in walkmenu(item)):
            attr = colors.color_menu_spec

        if level < len(sheet.activeMenuItems):
          if j == sheet.activeMenuItems[level]:
            attr = colors.color_menu_active

            if level < len(sheet.activeMenuItems):
                vd.drawSubmenu(scr, sheet, y+i, x+w+4, item.menus, level+1, disp_menu_boxchars=disp_menu_boxchars)

        menudraw(scr, y+i, x, ls, colors.color_menu)

        title = item.title
        pretitle= ' '
        titlenote= ' '
        if item.menus:
            titlenote = vd.options.disp_menu_more

        mainbinding = ''
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

        # actually display the menu item
        title += ' '*(w-len(pretitle)-len(item.title)+1) # padding

        menudraw(scr, y+i, x+1, pretitle+title, attr)
        if maxbinding and mainbinding:
            menudraw(scr, y+i, x+1+w-len(mainbinding), mainbinding, attr.update(colors.keystrokes))
        menudraw(scr, y+i, x+2+w, titlenote, attr)
        menudraw(scr, y+i, x+3+w, ls, colors.color_menu)

        vd.onMouse(scr, x, y+i, w+3, 1,
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


def _done(vd, *args, **kwargs):
    'Accept and execute current menu item (like pressing Enter).'
    return True


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
    scr.addstr(0, 0, ' '*(w-1), colors.color_menu.attr)
    disp_menu_boxchars = sheet.options.disp_menu_boxchars
    x = 1
    ymax = 4
    toplevel = sheet.menus
    for i, item in enumerate(toplevel):
        if sheet.activeMenuItems and i == sheet.activeMenuItems[0]:
            cattr = colors.color_menu_active
            vd.drawSubmenu(scr, sheet, 1, x, item.menus, 1, disp_menu_boxchars)
        else:
            cattr = colors.color_menu

        menutitle = ' ' + ''.join(f'[:underline]{ch}[/]' if ch.isupper() else ch for ch in item.title) + ' '
        menudraw(scr, 0, x, menutitle, cattr)

        vd.onMouse(scr, x, 0, dispwidth(item.title)+2, 1,
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

    currentItem = sheet.getMenuItem()
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
    menuh += len(sheet.getMenuItem(sheet.activeMenuItems[:-1]).menus)
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

    vd.onMouse(scr, helpx, menuy, helpw, y-menuy+1,
               BUTTON1_PRESSED=_done,
               BUTTON1_CLICKED=_done,
               BUTTON1_RELEASED=vd.nop,
               BUTTON2_RELEASED=vd.nop,
               BUTTON3_RELEASED=vd.nop)


@BaseSheet.api
def pressMenu(sheet, *args):
    '''Navigate to given menupath in *args* and activate menu if not already activated. Return True if pressing current item.
    Example: sheet.pressMenu("Help", "Version")
    '''
    ret = False
    p = _intMenuPath(sheet, args)
    if p == sheet.activeMenuItems:  # clicking on current menu item
        if sheet.getMenuItem(p).longname:
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

    def _clickedDuringMenu():
        r = vd.parseMouse(menu=vd.scrMenu, top=vd.winTop, bot=vd.winBottom)
        f = vd.getMouse(r.x, r.y, r.keystroke)
        if f:
            if f(r.y, r.x, r.keystroke):  # call each function until one returns a true-ish value
                return 'doit'
        else:
            return 'offmenu'

    try:
      while True:
        if len(sheet.activeMenuItems) < 2:
            sheet.activeMenuItems.append(0)

        vd.draw_all()

        k = vd.getkeystroke(vd.scrMenu, sheet)

        if not k:
            continue

        currentItem = sheet.getMenuItem()

        if k == 'Ctrl+[':  # ESC
            nEscapes += 1  #1470
            if nEscapes > 1:
                return
            continue
        else:
            nEscapes = 0

        if k in ['Ctrl+C', 'Ctrl+Q', 'q', 'Ctrl+H', 'Bksp']:
            return

        elif k in ['KEY_MOUSE']:
            r = _clickedDuringMenu()
            if r == 'offmenu':
                return  # clicking off the menu is an escape
            elif r == 'doit':
                break

        elif k in ['Right', 'l']:
            if currentItem.menus and sheet.activeMenuItems[1] != 0:  # not first item
                sheet.activeMenuItems.append(0)
            else:
                sheet.activeMenuItems = [sheet.activeMenuItems[0]+1, 0]

        elif k in ['Left', 'h']:
            if len(sheet.activeMenuItems) > 2:
                sheet.activeMenuItems.pop(-1)
            else:
                sheet.activeMenuItems = [sheet.activeMenuItems[0]-1, 0]

        elif k in ['Down', 'j']:
            sheet.activeMenuItems[-1] += 1

        elif k in ['Up', 'k']:
            sheet.activeMenuItems[-1] -= 1

        elif k in ['Enter', ' ']:
            if currentItem.menus:
                sheet.activeMenuItems.append(0)
            else:
                break

        elif k in main_menu.keys():
            sheet.pressMenu(main_menu[k])

        else:
            vd.warning(f'unknown keystroke {k}')

        sheet.checkMenu()

    finally:
        vd.menuRunning = False
        sheet.activeMenuItems = []
        vd.options.disp_menu=old_disp_menu

    vd.draw_all()
    sheet.execCommand(currentItem.longname)

main_menu = {'f': 'File', 'e': 'Edit', 'v': 'View', 'c': 'Column', 'r': 'Row', 'd': 'Data', 'p': 'Plot', 's': 'System', 'h': 'Help'}

BaseSheet.addCommand('Alt+f', 'menu-file', 'pressMenu("File")', '')
BaseSheet.addCommand('Alt+e', 'menu-edit', 'pressMenu("Edit")', '')
BaseSheet.addCommand('Alt+v', 'menu-view', 'pressMenu("View")', '')
BaseSheet.addCommand('Alt+c', 'menu-column', 'pressMenu("Column")', '')
BaseSheet.addCommand('Alt+r', 'menu-row', 'pressMenu("Row")', '')
BaseSheet.addCommand('Alt+d', 'menu-data', 'pressMenu("Data")', '')
BaseSheet.addCommand('Alt+p', 'menu-plot', 'pressMenu("Plot")', '')
BaseSheet.addCommand('Alt+s', 'menu-system', 'pressMenu("System")', '')
BaseSheet.addCommand('Alt+h', 'menu-help', 'pressMenu("Help")', 'open the Help menu')
BaseSheet.bindkey('Ctrl+H', 'menu-help')
BaseSheet.bindkey('Bksp', 'menu-help')

vd.addGlobals({'Menu': Menu})
