'''
Status messages get added with vd.{debug/aside/status/warning/fail/error}(), and cleared in mainloop
'''

import builtins
import collections
import curses
import sys

import visidata
from visidata import vd, VisiData, BaseSheet, Sheet, ColumnItem, Column, RowColorizer, options, colors, wrmap, clipdraw, ExpectedException, update_attr, dispwidth, ColorAttr


vd.option('disp_rstatus_fmt', '{sheet.threadStatus} {sheet.keystrokeStatus}   [:longname]{sheet.longname}[/]  {sheet.nRows:9d} {sheet.rowtype} {sheet.modifiedStatus}{sheet.selectedStatus}{vd.replayStatus}', 'right-side status format string')
vd.option('disp_status_fmt', '[:onclick sheets-stack]{sheet.shortcut}› {sheet.name}[/]| ', 'status line prefix')
vd.theme_option('disp_lstatus_max', 0, 'maximum length of left status line')
vd.theme_option('disp_status_sep', '│', 'separator between statuses')

vd.theme_option('color_keystrokes', 'bold white on 237', 'color of input keystrokes')
vd.theme_option('color_longname', '6', 'color of command longnames')
vd.theme_option('color_keys', 'bold', 'color of keystrokes in help')
vd.theme_option('color_status', 'bold on 238', 'status line color')
vd.theme_option('color_error', '202 1', 'error message color')
vd.theme_option('color_warning', '166 15', 'warning message color')
vd.theme_option('color_top_status', 'underline', 'top window status bar color')
vd.theme_option('color_active_status', 'black on 68 blue', ' active window status bar color')
vd.theme_option('color_inactive_status', '8 on black', 'inactive window status bar color')
vd.theme_option('color_highlight_status', 'black on green', 'color of highlighted elements in statusbar')

BaseSheet.init('longname', lambda: '')

@BaseSheet.api
def _updateStatusBeforeExec(sheet, cmd, args, ks):
    sheet.longname = cmd.longname
    if sheet._scr:
        vd.drawRightStatus(sheet._scr, sheet)  #996 show longname during commands
        sheet._scr.refresh()


vd.beforeExecHooks.append(BaseSheet._updateStatusBeforeExec)


@VisiData.lazy_property
def statuses(vd):
    return collections.OrderedDict()  # (priority, statusmsg) -> num_repeats; shown until next action


@VisiData.lazy_property
def statusHistory(vd):
    return list()  # list of [priority, statusmsg, repeats] for all status messages ever

@VisiData.api
def getStatusSource(vd):
    return None


@VisiData.api
def status(vd, *args, priority=0):
    'Display *args* on status until next action.'
    if not args:
        return True

    k = (priority, tuple(map(str, args)))
    vd.statuses[k] = vd.statuses.get(k, 0) + 1

    source = vd.getStatusSource()

    if not vd.cursesEnabled:
        msg = '\r' + composeStatus(args)
        if vd.options.debug:
            msg += f' [{source}]'
        builtins.print(msg, file=sys.stderr)

    return vd.addToStatusHistory(*args, priority=priority, source=source)

@VisiData.api
def addToStatusHistory(vd, *args, priority=0, source=None):
    if vd.statusHistory:
        prevpri, prevargs, _, _ = vd.statusHistory[-1]
        if prevpri == priority and prevargs == args:
            vd.statusHistory[-1][2] += 1
            return True

    vd.statusHistory.append([priority, args, 1, source])
    return True

@VisiData.api
def error(vd, *args):
    'Abort with ExpectedException, and display *args* on status as an error.'
    vd.status(*args, priority=3)
    raise ExpectedException(args[0] if args else '')

@VisiData.api
def fail(vd, *args):
    'Abort with ExpectedException, and display *args* on status as a warning.'
    vd.status(*args, priority=2)
    raise ExpectedException(args[0] if args else '')

@VisiData.api
def warning(vd, *args):
    'Display *args* on status as a warning.'
    vd.status(*args, priority=1)

@VisiData.api
def aside(vd, *args, priority=0):
    'Add a message to statuses without showing the message proactively.'
    return vd.addToStatusHistory(*args, priority=priority, source=vd.getStatusSource())

@VisiData.api
def debug(vd, *args, **kwargs):
    'Display *args* on status if options.debug is set.'
    if options.debug:
        return vd.status(*args, **kwargs)

def middleTruncate(s, w):
    if len(s) <= w:
        return s
    return s[:w] + options.disp_truncator + s[-w:]


def composeStatus(msgparts, n=1):
    msg = '; '.join(wrmap(str, msgparts))
    if n > 1:
        msg = '[%sx] %s' % (n, msg)
    return msg


@BaseSheet.api
def leftStatus(sheet):
    'Return left side of status bar for this sheet. Overridable.'
    return sheet.formatString(sheet.options.disp_status_fmt)


@VisiData.api
def drawLeftStatus(vd, scr, vs):
    'Draw left side of status bar.'
    cattr = colors.get_color('color_active_status')
    active = (vs is vd.activeSheet)
    if active:
        cattr = update_attr(cattr, colors.color_active_status, 1)
    else:
        cattr = update_attr(cattr, colors.color_inactive_status, 1)

    if scr is vd.winTop:
        cattr = update_attr(cattr, colors.color_top_status, 1)

    x = 0
    y = vs.windowHeight-1  # status for each window
    lstatus = vs.leftStatus()
    maxwidth = options.disp_lstatus_max
    if maxwidth > 0:
        lstatus = middleTruncate(lstatus, maxwidth//2)

    x = clipdraw(scr, y, 0, lstatus, cattr, w=vs.windowWidth-1)

    vd.onMouse(scr, 0, y, x, 1,
                    BUTTON3_PRESSED='rename-sheet',
                    BUTTON3_CLICKED='rename-sheet')


@VisiData.api
def rightStatus(vd, sheet):
    'Return right side of status bar.  Overridable.'
    return sheet.formatString(sheet.options.disp_rstatus_fmt)


@BaseSheet.property
def keystrokeStatus(vs):
    if vs is vd.activeSheet:
        return f'[:keystrokes]{vd.keystrokes}[/]'

    return ''


@BaseSheet.property
def threadStatus(vs) -> str:
    if vs.currentThreads:
        ret = str(vd.checkMemoryUsage())
        gerunds = [p.gerund for p in vs.progresses if p.gerund] or ['processing']
        ret += f' [:working]{vs.progressPct} {gerunds[0]}…[/]'
        return ret
    return ''

@BaseSheet.property
def modifiedStatus(sheet):
    ret = ' [M]' if sheet.hasBeenModified else ''
    if not vd.couldOverwrite():
        ret += ' [:highlight_status][RO][/] '
    return ret


@Sheet.property
def selectedStatus(sheet):
    if sheet.nSelectedRows:
        return f' [:selected_row][:onclick dup-selected]{sheet.options.disp_selected_note}{sheet.nSelectedRows}[/][/] '


@VisiData.api
def drawRightStatus(vd, scr, vs):
    'Draw right side of status bar.  Return length displayed.'
    rightx = vs.windowWidth

    statuslen = 0
    try:
        cattr = ColorAttr()
        if scr is vd.winTop:
            cattr = update_attr(cattr, colors.color_top_status, 0)
        cattr = update_attr(cattr, colors.color_active_status if vs is vd.activeSheet else colors.color_inactive_status, 0)
        rstat = vd.rightStatus(vs)
        x = max(2, rightx-dispwidth(rstat)-1)
        statuslen = clipdraw(scr, vs.windowHeight-1, x, rstat, cattr, w=vs.windowWidth-1)
    finally:
        if scr:
            curses.doupdate()
    return statuslen


class StatusSheet(Sheet):
    precious = False
    rowtype = 'statuses'  # rowdef: (priority, args, nrepeats)
    columns = [
        ColumnItem('priority', 0, type=int, width=0),
        ColumnItem('nrepeats', 2, type=int, width=0),
        ColumnItem('args', 1, width=0),
        Column('message', width=50, getter=lambda col,row: composeStatus(row[1], row[2])),
        ColumnItem('source', 3, max_help=1),
    ]
    colorizers = [
        RowColorizer(1, 'color_error', lambda s,c,r,v: r and r[0] == 3),
        RowColorizer(1, 'color_warning', lambda s,c,r,v: r and r[0] in [1,2]),
    ]

    def reload(self):
        self.rows = self.source


@VisiData.property
def statusHistorySheet(vd):
    return StatusSheet("status_history", source=vd.statusHistory[::-1])  # in reverse order


BaseSheet.addCommand('^P', 'open-statuses', 'vd.push(vd.statusHistorySheet)', 'open Status History')

vd.addMenuItems('''
    View > Statuses > open-statuses
''')
