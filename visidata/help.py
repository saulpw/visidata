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
        from pkg_resources import resource_filename
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
            if (keystrokes not in self.revbinds) and ('-' not in keystrokes or keystrokes[-1] == '-'):
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


@VisiData.global_api
def openManPage(vd):
    from pkg_resources import resource_filename
    import os
    with SuspendCurses():
        os.system(' '.join(['man', resource_filename(__name__, 'man/vd.1')]))


# in VisiData, ^H refers to the man page
globalCommand('^H', 'sysopen-help', 'openManPage()', 'view vd man page')
BaseSheet.addCommand('z^H', 'help-commands', 'vd.push(HelpSheet(name + "_commands", source=sheet, revbinds={}))', 'view sheet of command longnames and keybindings for current sheet')
BaseSheet.addCommand('gz^H', 'help-commands-all', 'vd.push(HelpSheet("all_commands", source=None, revbinds={}))', 'view sheet of command longnames and keybindings for all sheet types')
globalCommand(None, 'help-search', 'help_search(sheet, input("help: "))', 'search through command longnames with search terms')

BaseSheet.bindkey('KEY_F(1)', 'sysopen-help')
BaseSheet.bindkey('KEY_BACKSPACE', 'sysopen-help')
BaseSheet.bindkey('zKEY_F(1)', 'help-commands')
BaseSheet.bindkey('zKEY_BACKSPACE', 'help-commands')
