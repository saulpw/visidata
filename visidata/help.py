from pkg_resources import resource_filename

from visidata import *


class HelpSheet(MetaSheet):
    'Show all commands available to the source sheet.'
    rowtype = 'commands'
    precious = False
    _ordering = [('sheet', False), ('longname', False)]

    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('longname'),
        Column('keystrokes', getter=lambda col,row: col.sheet.revbinds.get(row.longname)),
        Column('description', getter=lambda col,row: col.sheet.cmddict[(row.sheet, row.longname)].helpstr),
        ColumnAttr('execstr', width=0),
        Column('logged', width=0, getter=lambda col,row: isLoggableCommand(row.longname)),
    ]
    nKeys = 2

    def iterload(self):
        cmdlist = VisiDataMetaSheet('cmdlist', source=None)

        self.cmddict = {}
        itcmds = vd.commands.iterall()
        for (k, o), v in itcmds:
            yield v
            v.sheet = o
            self.cmddict[(v.sheet, v.longname)] = v

        for cmdrow in cmdlist.rows:
            k = (cmdrow.sheet, cmdrow.longname)
            if k in self.cmddict:
                self.cmddict[k].helpstr = cmdrow.helpstr

        self.revbinds = {}  # [longname] -> keystrokes
        itbindings = vd.bindkeys.iterall()
        for (keystrokes, _), longname in itbindings:
            if (keystrokes not in self.revbinds) and not vd.isLongname(keystrokes):
                self.revbinds[longname] = keystrokes


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
        self._shown = False
        self.amgr = visidata.AnimationMgr()

    @property
    def shown(self):
        return self._shown

    @shown.setter
    def shown(self, v):
        self._shown = v
        if v:
            self.amgr.trigger(self.name, loop=True, y=1, x=2)

    def draw(self, scr, x=None, y=None):
        if not self.shown:
            if self.scr:
                self.scr.erase()
                self.scr.refresh()
            return
        if y is None: y=0  # show at top of screen by default
        if not self.scr or scr is not self.parentscr:  # (re)allocate help pane scr
            if y+self.amgr.maxHeight+3 < scr.getmaxyx()[0]:
                yhelp = y+1
            else:
                yhelp = y-self.amgr.maxHeight-3

            self.scr = scr.derwin(self.amgr.maxHeight+3, self.amgr.maxWidth+4, yhelp, 0)
            self.parentscr = scr

        if self.amgr.active:
            self.scr.erase()
            self.scr.box()
            self.amgr.draw(self.scr)
            self.scr.refresh()


@VisiData.api
def getHelpPane(vd, name, module='vdplus'):
    ret = HelpPane(name)
    try:
        ret.amgr.load(name, Path(resource_filename(module, 'help/'+name+'.ddw')).open_text())
    except FileNotFoundError:
        pass
    except ModuleNotFoundError:
        pass
    return ret


@VisiData.global_api
def openManPage(vd):
    import os
    with SuspendCurses():
        if os.system(' '.join(['man', resource_filename(__name__, 'man/vd.1')])) != 0:
            vd.push(TextSheet('man_vd', source=Path(resource_filename(__name__, 'man/vd.txt'))))


# in VisiData, ^H refers to the man page
globalCommand('^H', 'sysopen-help', 'openManPage()', 'view vd man page')
BaseSheet.addCommand('z^H', 'help-commands', 'vd.push(HelpSheet(name + "_commands", source=sheet, revbinds={}))', 'view sheet of command longnames and keybindings for current sheet')
BaseSheet.addCommand('gz^H', 'help-commands-all', 'vd.push(HelpSheet("all_commands", source=None, revbinds={}))', 'view sheet of command longnames and keybindings for all sheet types')
globalCommand(None, 'help-search', 'help_search(sheet, input("help: "))', 'search through command longnames with search terms')

BaseSheet.bindkey('KEY_F(1)', 'sysopen-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'sysopen-help')
BaseSheet.bindkey('zKEY_F(1)', 'help-commands')
BaseSheet.bindkey('zKEY_BACKSPACE', 'help-commands')
