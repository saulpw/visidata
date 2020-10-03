import collections
import curses

from visidata import vd, VisiData, BaseSheet, Sheet, ColumnItem, Column, RowColorizer, options, colors, wrmap, clipdraw, ExpectedException, update_attr, theme


__all__ = ['StatusSheet', 'status', 'error', 'fail', 'warning', 'debug']

theme('disp_rstatus_fmt', ' {sheet.longname} {sheet.nRows:9d} {sheet.rowtype} ', 'right-side status format string')
theme('disp_status_fmt', '{sheet.shortcut}› {sheet.name}| ', 'status line prefix')
theme('disp_lstatus_max', 0, 'maximum length of left status line')
theme('disp_status_sep', ' | ', 'separator between statuses')

theme('color_keystrokes', 'white', 'color of input keystrokes on status line')
theme('color_status', 'bold', 'status line color')
theme('color_error', 'red', 'error message color')
theme('color_warning', 'yellow', 'warning message color')
theme('color_top_status', 'underline', 'top window status bar color')
theme('color_active_status', 'bold', ' active window status bar color')
theme('color_inactive_status', '8', 'inactive window status bar color')

BaseSheet.init('longname', lambda: '')

vd.beforeExecHooks.append(lambda sheet, cmd, args, ks: setattr(sheet, 'longname', cmd.longname))

@VisiData.lazy_property
def statuses(vd):
    return collections.OrderedDict()  # (priority, statusmsg) -> num_repeats; shown until next action


@VisiData.lazy_property
def statusHistory(vd):
    return list()  # list of [priority, statusmsg, repeats] for all status messages ever


@VisiData.global_api
def status(self, *args, priority=0):
    'Display *args* on status until next action.'
    if not args:
        return True

    k = (priority, args)
    self.statuses[k] = self.statuses.get(k, 0) + 1

    if self.statusHistory:
        prevpri, prevargs, prevn = self.statusHistory[-1]
        if prevpri == priority and prevargs == args:
            self.statusHistory[-1][2] += 1
            return True

    self.statusHistory.append([priority, args, 1])
    return True

@VisiData.global_api
def error(vd, *args):
    'Abort with ExpectedException, and display *args* on status as an error.'
    vd.status(*args, priority=3)
    raise ExpectedException(args[0] if args else '')

@VisiData.global_api
def fail(vd, *args):
    'Abort with ExpectedException, and display *args* on status as a warning.'
    vd.status(*args, priority=2)
    raise ExpectedException(args[0] if args else '')

@VisiData.global_api
def warning(vd, *args):
    'Display *args* on status as a warning.'
    vd.status(*args, priority=1)

@VisiData.global_api
def debug(vd, *args, **kwargs):
    'Display *args* on status if options.debug is set.'
    if options.debug:
        return vd.status(*args, **kwargs)

def middleTruncate(s, w):
    if len(s) <= w:
        return s
    return s[:w] + options.disp_truncator + s[-w:]


def composeStatus(msgparts, n):
    msg = '; '.join(wrmap(str, msgparts))
    if n > 1:
        msg = '[%sx] %s' % (n, msg)
    return msg


@BaseSheet.api
def leftStatus(sheet):
    'Return left side of status bar for this sheet. Overridable.'
    return options.disp_status_fmt.format(sheet=sheet, vd=vd)


@VisiData.api
def drawLeftStatus(vd, scr, vs):
    'Draw left side of status bar.'
    cattr = colors.get_color('color_status')
    active = vs is vd.sheets[0]  # active sheet
    if active:
        cattr = update_attr(cattr, colors.color_active_status, 0)
    else:
        cattr = update_attr(cattr, colors.color_inactive_status, 0)

    if scr is vd.winTop:
        cattr = update_attr(cattr, colors.color_top_status, 1)

    attr = cattr.attr
    error_attr = update_attr(cattr, colors.color_error, 1).attr
    warn_attr = update_attr(cattr, colors.color_warning, 2).attr
    sep = options.disp_status_sep

    x = 0
    y = vs.windowHeight-1  # status for each window
    try:
        lstatus = vs.leftStatus()
        maxwidth = options.disp_lstatus_max
        if maxwidth > 0:
            lstatus = middleTruncate(lstatus, maxwidth//2)

        x = clipdraw(scr, y, 0, lstatus, attr, w=vs.windowWidth-1)

        vd.onMouse(scr, y, 0, 1, x,
                        BUTTON1_PRESSED='sheets',
                        BUTTON3_PRESSED='rename-sheet',
                        BUTTON3_CLICKED='rename-sheet')
    except Exception as e:
        vd.exceptionCaught(e)

    if not active:
        return

    one = False
    for (pri, msgparts), n in sorted(vd.statuses.items(), key=lambda k: -k[0][0]):
        try:
            if x > vs.windowWidth:
                break
            if one:  # any messages already:
                x += clipdraw(scr, y, x, sep, attr, w=vs.windowWidth-x)
            one = True
            msg = composeStatus(msgparts, n)

            if pri == 3: msgattr = error_attr
            elif pri == 2: msgattr = warn_attr
            elif pri == 1: msgattr = warn_attr
            else: msgattr = attr
            x += clipdraw(scr, y, x, msg, msgattr, w=vs.windowWidth-x)
        except Exception as e:
            vd.exceptionCaught(e)


@VisiData.api
def rightStatus(vd, sheet):
    'Return right side of status bar.  Overrideable.'
    return options.disp_rstatus_fmt.format(sheet=sheet, vd=vd)


@VisiData.api
def drawRightStatus(vd, scr, vs):
    'Draw right side of status bar.  Return length displayed.'
    rightx = vs.windowWidth

    ret = 0
    statcolors = [
        (vd.rightStatus(vs), 'color_status'),
    ]

    active = vs is vd.sheets[0]  # active sheet

    if active:
        statcolors.append((vd.keystrokes or '', 'color_keystrokes'))

    if vs.currentThreads:
        statcolors.insert(0, vd.checkMemoryUsage())
        if vs.progresses:
            gerund = vs.progresses[0].gerund
        else:
            gerund = 'processing'
        statcolors.insert(1, ('  %s %s…' % (vs.progressPct, gerund), 'color_status'))

    if active and vd.currentReplay:
        statcolors.insert(0, (vd.replayStatus, 'color_status_replay'))

    for rstatcolor in statcolors:
        if rstatcolor:
            try:
                rstatus, coloropt = rstatcolor
                rstatus = ' '+rstatus
                cattr = colors.get_color(coloropt)
                if scr is vd.winTop:
                    cattr = update_attr(cattr, colors.color_top_status, 0)
                if active:
                    cattr = update_attr(cattr, colors.color_active_status, 0)
                else:
                    cattr = update_attr(cattr, colors.color_inactive_status, 0)
                statuslen = clipdraw(scr, vs.windowHeight-1, rightx, rstatus, cattr.attr, w=vs.windowWidth-1, rtl=True)
                rightx -= statuslen
                ret += statuslen
            except Exception as e:
                vd.exceptionCaught(e)

    if scr:
        curses.doupdate()
    return ret


class StatusSheet(Sheet):
    precious = False
    rowtype = 'statuses'  # rowdef: (priority, args, nrepeats)
    columns = [
        ColumnItem('priority', 0, type=int, width=0),
        ColumnItem('nrepeats', 2, type=int, width=0),
        ColumnItem('args', 1, width=0),
        Column('message', getter=lambda col,row: composeStatus(row[1], row[2])),
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
