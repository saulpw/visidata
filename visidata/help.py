from pkg_resources import resource_filename

from visidata import *

vd.show_help = False


@VisiData.api
class HelpSheet(MetaSheet):
    'Show all commands available to the source sheet.'
    rowtype = 'commands'
    precious = False
    _ordering = [('sheet', False), ('longname', False)]

    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('longname'),
        Column('keystrokes', getter=lambda col,row: col.sheet.revbinds.get(row.longname, [None])[0]),
        Column('all_bindings', width=0, getter=lambda col,row: list(set(col.sheet.revbinds.get(row.longname, [])))),
        Column('description', getter=lambda col,row: col.sheet.cmddict[(row.sheet, row.longname)].helpstr),
        ColumnAttr('execstr', width=0),
        Column('logged', width=0, getter=lambda col,row: vd.isLoggableCommand(row.longname)),
    ]
    nKeys = 2

    def iterload(self):
        cmdlist = VisiDataMetaSheet('cmdlist', source=None)

        self.cmddict = {}
        if self.source:
            itcmds = vd.commands.iter(obj=self.source)
        else:
            itcmds = vd.commands.iterall()

        for (k, o), v in itcmds:
            yield v
            v.sheet = o
            self.cmddict[(v.sheet, v.longname)] = v

        for cmdrow in cmdlist.rows:
            k = (cmdrow.sheet, cmdrow.longname)
            if k in self.cmddict:
                self.cmddict[k].helpstr = cmdrow.helpstr

    @BaseSheet.lazy_property
    def revbinds(self):
        revbinds = collections.defaultdict(list)  # longname -> [keystrokes, ..]
        itbindings = vd.bindkeys.iterall()
        for (keystrokes, _), longname in itbindings:
            revbinds[longname].append(keystrokes)

        return revbinds


@VisiData.api
@asyncthread
def help_search(vd, sheet, regex):
    vs = HelpSheet(source=None)
    vs.rows = []  # do not trigger push reload
    vd.push(vs)   # push first, then reload
    vd.sync(vs.reload())

    # find rows matching regex on original HelpSheet
    rowidxs = list(vd.searchRegex(vs, regex=regex, columns="visibleCols"))

    # add only matching rows
    allrows = vs.rows
    vs.rows = []
    for rowidx in rowidxs:
        vs.addRow(allrows[rowidx])


class HelpPane:
    def __init__(self, name):
        self.name = name
        self.scr = None
        self.parentscr = None
        self.amgr = visidata.AnimationMgr()

    def draw(self, scr, x=None, y=None):
        if not scr: return
        if not vd.show_help:
            if self.scr:
                self.scr.erase()
                self.scr.refresh()
                self.scr = None
            return
        if y is None: y=0  # show at top of screen by default
        if x is None: x=0
        if not self.scr or scr is not self.parentscr:  # (re)allocate help pane scr
            if y >= 0:
                if y+self.amgr.maxHeight+3 < scr.getmaxyx()[0]:
                    yhelp = y+1
                else:
                    yhelp = y-self.amgr.maxHeight-3
            else:  # y<0
                yhelp = scr.getmaxyx()[0]-self.amgr.maxHeight-4

            if x >= 0:
                if x+self.amgr.maxWidth+4 < scr.getmaxyx()[1]:
                    xhelp = x+1
                else:
                    xhelp = x-self.amgr.maxWidth-4
            else:  # x<0
                xhelp = scr.getmaxyx()[1]-self.amgr.maxWidth-5

            self.scr = scr.derwin(self.amgr.maxHeight+3, self.amgr.maxWidth+4, yhelp, xhelp)
            self.parentscr = scr

        self.scr.erase()
        self.scr.box()
        self.amgr.draw(self.scr, y=1, x=2)
        self.scr.refresh()


@VisiData.api
@functools.lru_cache(maxsize=None)
def getHelpPane(vd, name, module='vdplus'):
    ret = HelpPane(name)
    try:
        ret.amgr.load(name, Path(resource_filename(module,'ddw/'+name+'.ddw')).open_text(encoding='utf-8'))
        ret.amgr.trigger(name, loop=True)
    except FileNotFoundError as e:
        vd.debug(str(e))
    except ModuleNotFoundError as e:
        vd.debug(str(e))
    except KeyError as e:
        vd.debug(str(e))
    return ret


@VisiData.api
def openManPage(vd):
    import os
    with SuspendCurses():
        if os.system(' '.join(['man', resource_filename(__name__, 'man/vd.1')])) != 0:
            vd.push(TextSheet('man_vd', source=Path(resource_filename(__name__, 'man/vd.txt'))))


# in VisiData, g^H refers to the man page
BaseSheet.addCommand('g^H', 'sysopen-help', 'openManPage()', 'Show the UNIX man page for VisiData')
BaseSheet.addCommand('z^H', 'help-commands', 'vd.push(HelpSheet(name + "_commands", source=sheet, revbinds={}))', 'list commands and keybindings available on current sheet')
BaseSheet.addCommand('gz^H', 'help-commands-all', 'vd.push(HelpSheet("all_commands", source=None, revbinds={}))', 'list commands and keybindings for all sheet types')
BaseSheet.addCommand(None, 'help-search', 'help_search(sheet, input("help: "))', 'search through command longnames with search terms')

BaseSheet.bindkey('KEY_F(1)', 'sysopen-help')
BaseSheet.bindkey('zKEY_F(1)', 'help-commands')
BaseSheet.bindkey('zKEY_BACKSPACE', 'help-commands')

HelpSheet.addCommand(ENTER, 'exec-command', 'quit(sheet); draw_all(); activeStack[0].execCommand(cursorRow.longname)', 'execute command on undersheet')
BaseSheet.addCommand(None, 'open-tutorial-visidata', 'launchBrowser("https://jsvine.github.io/intro-to-visidata/")', 'open https://jsvine.github.io/intro-to-visidata/')

vd.addMenuItem("Help", "VisiData tutorial", 'open-tutorial-visidata')
vd.addMenuItem("Help", 'Sheet commands', 'help-commands')
vd.addMenuItem("Help", 'All commands', 'help-commands-all')
