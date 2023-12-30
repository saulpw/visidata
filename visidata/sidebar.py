from typing import Optional, Union
import textwrap

from visidata import vd, VisiData, BaseSheet, colors, TextSheet, clipdraw, wraptext, dispwidth, AttrDict, wrmap
from visidata import CommandHelpGetter, OptionHelpGetter


vd.option('disp_sidebar', True, 'whether to display sidebar')
vd.option('disp_sidebar_fmt', '{guide}', 'format string for default sidebar')
vd.theme_option('disp_sidebar_width', 0, 'max width for sidebar')
vd.theme_option('disp_sidebar_height', 0, 'max height for sidebar')
vd.theme_option('color_sidebar', 'black on 114 blue', 'base color of sidebar')
vd.theme_option('color_sidebar_title', 'black on yellow', 'color of sidebar title')

@BaseSheet.property
def formatter_helpstr(sheet):
    return AttrDict(commands=CommandHelpGetter(type(sheet)),
                    options=OptionHelpGetter())


@BaseSheet.property
def default_sidebar(sheet):
    'Default to format options.disp_sidebar_fmt.  Overridable.'
    fmt = sheet.options.disp_sidebar_fmt
    return sheet.formatString(fmt, help=sheet.formatter_helpstr)


@VisiData.property
def recentStatusMessages(vd) -> str:
    r = ''
    for (pri, msgparts), n in vd.statuses.items():
        msg = '; '.join(wrmap(str, msgparts))
        msg = f'[{n}x] {msg}' if n > 1 else msg

        if pri == 3: msgattr = '[:error]'
        elif pri == 2: msgattr = '[:warning]'
        elif pri == 1: msgattr = '[:warning]'
        else: msgattr = ''

        if msgattr:
            r += '\n' + f'{msgattr}{msg}[/]'
        else:
            r += '\n' + msg

    if r:
        return '# statuses' + r

    return ''


@VisiData.api
def drawSidebar(vd, scr, sheet):
    sidebar = vd.recentStatusMessages
    bottommsg = ''
    overflowmsg = '[:reverse] Ctrl+P to view all status messages [/]'
    try:
        if not sidebar and sheet.options.disp_sidebar:
            sidebar = sheet.default_sidebar
            if not sidebar and sheet.options.disp_help > 0:
                sidebar = sheet.formatString(sheet.guide, help=sheet.formatter_helpstr)

            if sheet.options.disp_help < 0:
                bottommsg = '[:onclick sidebar-toggle][:reverse][x][:]'
                overflowmsg = '[:onclick open-sidebar]…↓…[/]'
            else:
                bottommsg = '[:onclick sidebar-toggle][:reverse] b to toggle sidebar [:]'
                overflowmsg = '[:reverse] see full sidebar with [:code]gb[/] [:]'
    except Exception as e:
        vd.exceptionCaught(e)
        sidebar = f'# error\n{e}'

    sheet.current_sidebar = sidebar

    return sheet.drawSidebarText(scr, text=sheet.current_sidebar, overflowmsg=overflowmsg, bottommsg=bottommsg)

@BaseSheet.api
def drawSidebarText(sheet, scr, text:Union[None,str,'HelpPane'], title:str='', overflowmsg:str='', bottommsg:str=''):
    scrh, scrw = scr.getmaxyx()
    maxw = sheet.options.disp_sidebar_width or scrw//2
    maxh = sheet.options.disp_sidebar_height or scrh-2

    cattr = colors.get_color('color_sidebar')

    text = text or ''

    if hasattr(text, 'draw'):  # like a HelpPane
        maxlinew = text.width
        winh = min(maxh, text.height+2)+1
    else:
        text = textwrap.dedent(text.strip('\n'))

        if not text:
            return

        lines = text.splitlines()
        if not title and lines and lines[0].strip().startswith('# '):
            title = lines[0].strip()[2:]
            text = '\n'.join(lines[1:])

        if not text:
            return

        lines = list(wraptext(text, width=maxw-4))
        maxlinew = 0
        if lines:
            maxlinew = max(maxlinew, max(dispwidth(textonly, maxwidth=maxw) for line, textonly in lines))
        winh = min(maxh, len(lines)+2)

    titlew = dispwidth(title)

    maxlinew = max(maxlinew, dispwidth(overflowmsg)+4)
    maxlinew = max(maxlinew, dispwidth(bottommsg)+4)
    maxlinew = max(maxlinew, titlew)
    winw = min(maxw, maxlinew+4)
    x, y, w, h = scrw-winw-1, scrh-winh-1, winw, winh

    sidebarscr = vd.subwindow(scr, x, y, w, h)

    sidebarscr.erase()
    sidebarscr.bkgd(' ', cattr.attr)
    sidebarscr.border()
    vd.onMouse(sidebarscr, 0, 0, w, h, BUTTON1_RELEASED='no-op', BUTTON1_PRESSED='no-op')

    if hasattr(text, 'draw'):  # like a HelpPane
        text.draw(sidebarscr, attr=cattr)
    else:
        i = 0
        for line, _ in lines:
            if i >= h-2:
                bottommsg = overflowmsg
                break

            x += clipdraw(sidebarscr, i+1, 2, line, cattr, w=w-3)
            i += 1

    x = max(0, w-titlew-6)
    clipdraw(sidebarscr, 0, x, f"|[:sidebar_title] {title} [:]|", cattr, w=titlew+4)
    if bottommsg:
        clipdraw(sidebarscr, h-1, winw-dispwidth(bottommsg)-4, '|'+bottommsg+'|[:]', cattr)

    sidebarscr.refresh()


@VisiData.api
class SidebarSheet(TextSheet):
    guide = '''
        # Sidebar Guide
        The sidebar provides additional information about the current sheet, defaulting to a basic guide to the current sheet type.
        It can be configured to show many useful attributes via `options.disp_sidebar_fmt`.

        - `gb` to open the sidebar in a new sheet
        - `b` to toggle the sidebar on/off for the current sheet
    '''

BaseSheet.addCommand('b', 'sidebar-toggle', 'sheet.options.disp_sidebar = not sheet.options.disp_sidebar', 'toggle sidebar on/off')
BaseSheet.addCommand('gb', 'open-sidebar', 'sheet.current_sidebar = "" if not hasattr(sheet, "current_sidebar") else sheet.current_sidebar; vd.push(SidebarSheet(name, options.disp_sidebar_fmt, source=sheet.current_sidebar.splitlines()))', 'open sidebar in new sheet')


vd.addMenuItems('''
    View > Sidebar > toggle > sidebar-toggle
    View > Sidebar > open in new sheet > open-sidebar
''')
