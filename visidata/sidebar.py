from typing import Optional
import textwrap

from visidata import vd, VisiData, BaseSheet, colors, TextSheet, clipdraw, wraptext, dispwidth


vd.option('disp_sidebar', True, 'whether to display sidebar')
vd.option('disp_sidebar_fmt', '{help}', 'format string for default sidebar')
vd.option('disp_sidebar_width', 0, 'max width for sidebar')
vd.option('disp_sidebar_height', 0, 'max height for sidebar')
vd.option('color_sidebar', 'black on 114 blue', 'base color of sidebar')


@BaseSheet.property
def sidebar(sheet):
    'Default to format options.disp_sidebar_fmt.  Overridable.'
    fmt = sheet.options.disp_sidebar_fmt
    return sheet.formatString(fmt)


@VisiData.api
def drawSidebar(vd, scr, sheet):
    sidebar = vd.recentStatusMessages
    bottommsg = ''
    overflowmsg = '[:reverse] Ctrl+P to view all status messages [/]'
    try:
        if not sidebar and sheet.options.disp_sidebar:
            sidebar = sheet.sidebar
            if not sidebar and sheet.options.disp_help > 0:
                sidebar = sheet.formatString(sheet.help)

            if sheet.options.disp_help < 0:
                bottommsg = '[:onclick sidebar-toggle][:reverse][x][:]'
                overflowmsg = '[:onclick open-sidebar]…↓…[/]'
            else:
                bottommsg = '[:onclick sidebar-toggle][:reverse] b to toggle sidebar [:]'
                overflowmsg = '[:reverse] (see full sidebar with [:code]gb[:reverse]) [:]'
    except Exception as e:
        vd.exceptionCaught(e)
        sidebar = f'# error\n{e}'

    return sheet.drawSidebarText(scr, text=sidebar, overflowmsg=overflowmsg, bottommsg=bottommsg)

@BaseSheet.api
def drawSidebarText(sheet, scr, text:Optional[str], title:str='', overflowmsg:str='', bottommsg:str=''):
    scrh, scrw = scr.getmaxyx()
    maxw = sheet.options.disp_sidebar_width or scrw//2
    maxh = sheet.options.disp_sidebar_height or scrh-2

    text = text or ''
    text = textwrap.dedent(text.strip('\n'))

    if not text:
        return

    lines = text.splitlines()
    if not title and lines and lines[0].strip().startswith('# '):
        title = lines[0][1:].strip()
        text = '\n'.join(lines[1:])

    titlew = dispwidth(title)

    cattr = colors.get_color('color_sidebar')
    lines = list(wraptext(text, width=maxw-4))
    maxlinew = titlew
    maxlinew = max(titlew, max(dispwidth(textonly, maxwidth=maxw) for line, textonly in lines))
    maxlinew = max(maxlinew, dispwidth(overflowmsg)+4)
    maxlinew = max(maxlinew, dispwidth(bottommsg)+4)
    winw = min(maxw, maxlinew+4)
    winh = min(maxh, len(lines)+2)
    x, y, w, h = scrw-winw-1, scrh-winh-1, winw, winh

    sidebarscr = vd.subwindow(scr, x, y, w, h)

    sidebarscr.erase()
    sidebarscr.bkgd(' ', cattr.attr)
    sidebarscr.border()
    vd.onMouse(sidebarscr, 0, 0, w, h, BUTTON1_RELEASED='no-op', BUTTON1_PRESSED='no-op')

    i = 0
    for line, _ in lines:
        if i >= h-2:
            bottommsg = overflowmsg
            break

        x += clipdraw(sidebarscr, i+1, 2, line, cattr, w=w-3)
        i += 1

    x = max(0, w-titlew-6)
    clipdraw(sidebarscr, 0, x, f"|[:black on yellow] {title} [:]|", cattr, w=titlew+4)
    if bottommsg:
        clipdraw(sidebarscr, h-1, winw-dispwidth(bottommsg)-4, '|'+bottommsg+'|[:]', cattr)

    sidebarscr.refresh()


@VisiData.api
class SidebarSheet(TextSheet):
    help = '''
        # Sidebar Guide
        The sidebar provides additional information about the current sheet, defaulting to a basic guide to the current sheet type.
        It can be configured to show many useful attributes via `options.disp_sidebar_fmt`.

        - `gb` to open the sidebar in a new sheet
        - `b` to toggle the sidebar on/off for the current sheet
    '''

BaseSheet.addCommand('b', 'sidebar-toggle', 'sheet.options.disp_sidebar = not sheet.options.disp_sidebar', 'toggle sidebar on/off')
BaseSheet.addCommand('gb', 'open-sidebar', 'vd.push(SidebarSheet(name, options.disp_sidebar_fmt, source=sidebar.splitlines()))', 'open sidebar in new sheet')


vd.addMenuItems('''
    View > Sidebar > toggle > sidebar-toggle
    View > Sidebar > open in new sheet > open-sidebar
''')
