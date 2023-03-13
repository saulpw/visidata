import textwrap

from visidata import vd, VisiData, BaseSheet, colorpanel, colors, TextSheet


vd.option('disp_sidebar_fmt', '{help}', 'format string for default sidebar')
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
    try:
        sidebar_title = ''
        sidebar = vd.recentStatusMessages or sheet.sidebar
    except Exception as e:
        vd.exceptionCaught(e)
        sidebar_title = 'error'
        sidebar = str(e)

    scrh, scrw = scr.getmaxyx()
    maxw = scrw//2
    maxh = scrh-2
    def _place(maxlinew, nlines):
        winw = min(maxw, maxlinew+4)
        winh = min(maxh, nlines+1)
        return (scrw-winw-1, scrh-winh-1, winw, winh)

    colorpanel(scr, sidebar, maxw, colors.get_color('color_sidebar'), _place)


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
