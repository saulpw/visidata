import textwrap

from visidata import vd, VisiData, BaseSheet, colors, TextSheet, clipdraw, wraptext, dispwidth


vd.option('disp_sidebar_fmt', '{help}', 'format string for default sidebar')
vd.option('disp_sidebar_width', 0, 'max width for sidebar')
vd.option('disp_sidebar_height', 0, 'max height for sidebar')
vd.option('color_sidebar', 'black on 114 blue', 'base color of sidebar')


@BaseSheet.property
def sidebar(sheet):
    'Default to format options.disp_sidebar_fmt.  Overridable.'
    fmt = sheet.options.disp_sidebar_fmt
    if fmt == '{help}':
        fmt = sheet.help
    return textwrap.dedent(sheet.formatString(fmt).strip('\n'))


@VisiData.api
def drawSidebar(vd, scr, sheet):
    sidebar_title = ''
    sidebar = vd.recentStatusMessages
    bottommsg = ''
    overflowmsg = '[:reverse] Ctrl+P to view all status messages [:]'
    try:
        if not sidebar:
            sidebar = sheet.sidebar
            bottommsg = '[:reverse] b to [:onclick sidebar-toggle]toggle sidebar[:]'
            overflowmsg = '[:reverse] (see full sidebar with [:code]gb[:reverse]) [:]'

        lines = sidebar.splitlines()
        if lines and lines[0].strip().startswith('# '):
            sidebar_title = lines[0][1:].strip()
            sidebar = '\n'.join(lines[1:])
    except Exception as e:
        vd.exceptionCaught(e)
        sidebar_title = 'error'
        sidebar = str(e)

    scrh, scrw = scr.getmaxyx()
    maxw = sheet.options.disp_sidebar_width or scrw//2
    maxh = sheet.options.disp_sidebar_height or scrh-2

    if not sidebar:
        return

    cattr = colors.get_color('color_sidebar')
    lines = list(wraptext(sidebar, width=maxw-4))
    maxlinew = max(dispwidth(textonly, maxwidth=maxw) for line, textonly in lines)
    maxlinew = max(maxlinew, dispwidth(overflowmsg)+4)
    maxlinew = max(maxlinew, dispwidth(bottommsg)+4)
    winw = min(maxw, maxlinew+4)
    winh = min(maxh, len(lines)+2)
    x, y, w, h = scrw-winw-1, scrh-winh-1, winw, winh

    sidebarscr = vd.subwindow(scr, h, w, y, x)

    sidebarscr.erase()
    sidebarscr.bkgd(cattr.attr)
    sidebarscr.border()
    vd.onMouse(sidebarscr, 0, 0, h, w, BUTTON1_RELEASED='no-op', BUTTON1_PRESSED='no-op')

    i = 0
    for line, _ in lines:
        if i >= h-2:
            bottommsg = overflowmsg
            break

        x += clipdraw(sidebarscr, i+1, 2, line, cattr, w=w-2)
        i += 1

    x = w-len(sidebar_title)-6
    clipdraw(sidebarscr, 0, x, f"|[:black on yellow] {sidebar_title} [:]|", cattr)
    if bottommsg:
        clipdraw(sidebarscr, h-1, winw-dispwidth(bottommsg)-4, '|'+bottommsg+'|[:]', cattr)


@BaseSheet.api
def sidebar_toggle(sheet):
    v = sheet.options.disp_sidebar_fmt
    v = '{help}' if not v else ''
    sheet.options.disp_sidebar_fmt = v


@VisiData.api
class SidebarSheet(TextSheet):
    help = '''
        # Sidebar Guide
        The sidebar provides additional information about the current sheet, defaulting to a basic guide to the current sheet type.
        It can be configured to show many useful attributes via `options.disp_sidebar_fmt`.

        - `gb` to open the sidebar in a new sheet
        - `b` to toggle the sidebar on/off for the current sheet
    '''

BaseSheet.addCommand('b', 'sidebar-toggle', 'sidebar_toggle()', 'toggle sidebar on/off')
BaseSheet.addCommand('gb', 'open-sidebar', 'vd.push(SidebarSheet(name, options.disp_sidebar_fmt, source=sidebar.splitlines()))', 'open sidebar in new sheet')


vd.addMenuItems('''
    View > Sidebar > toggle > sidebar-toggle
    View > Sidebar > open in new sheet > open-sidebar
''')
