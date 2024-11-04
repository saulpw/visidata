import functools
import collections

from visidata import VisiData, MetaSheet, ColumnAttr, Column, BaseSheet, VisiDataMetaSheet, SuspendCurses
from visidata import vd, asyncthread, ENTER, drawcache, AttrDict, TextSheet

vd.option('disp_expert', 0, 'max level of options and columns to include')

@BaseSheet.api
def hint_basichelp(sheet):
    return 0, 'Alt+H to open the [:underline]H[/]elp menu'


@VisiData.api
def iterMenuPaths(vd, item=None, menupath=[]):
    'Generate (longname, menupath).'
    if item is None:
        item = vd.menus

    if isinstance(item, (list, tuple)):
        for m in item:
            yield from vd.iterMenuPaths(m, menupath)
    elif item.longname:
        yield item.longname, ' > '.join(menupath+[item.title])
    else:
        yield from vd.iterMenuPaths(item.menus, menupath+[item.title])


@VisiData.property
@drawcache
def menuPathsByLongname(vd):
    return dict(vd.iterMenuPaths())


@VisiData.api
class HelpSheet(MetaSheet):
    'Show all commands available to the source sheet.'
    rowtype = 'commands'
    precious = False
    _ordering = [('sheet', False), ('longname', False)]

    columns = [
        ColumnAttr('sheet'),
        ColumnAttr('module'),
        ColumnAttr('longname'),
        Column('menupath', width=0, cache=True, getter=lambda col,row: vd.menuPathsByLongname.get(row.longname, None)),
        Column('keystrokes', getter=lambda col,row: col.sheet.revbinds.get(row.longname, [None])[0]),
        Column('all_bindings', width=0, cache=True, getter=lambda col,row: list(set(col.sheet.revbinds.get(row.longname, [])))),
        Column('description', width=70, getter=lambda col,row: col.sheet.cmddict[(row.sheet, row.longname)].helpstr),
        ColumnAttr('execstr', width=0),
        Column('logged', width=0, getter=lambda col,row: vd.isLoggableCommand(row)),
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


class HelpPane:
    def __init__(self, name):
        import visidata
        self.name = name
        self.scr = None
        self.parentscr = None
        self.amgr = visidata.AnimationMgr()

    @property
    def width(self):
        return self.amgr.maxWidth

    @property
    def height(self):
        return self.amgr.maxHeight

    def draw(self, scr, x=None, y=None, **kwargs):
        if not scr: return
#        if vd.options.disp_help <= 0:
#            if self.scr:
#                self.scr.erase()
#                self.scr.refresh()
#                self.scr = None
#            return
        if y is None: y=0  # show at top of screen by default
        if x is None: x=0
        hneeded = self.amgr.maxHeight+3
        wneeded = self.amgr.maxWidth+4
        scrh, scrw = scr.getmaxyx()
        if not self.scr or scr is not self.parentscr:  # (re)allocate help pane scr
            if y >= 0:
                if y+hneeded < scrh:
                    yhelp = y+1
                else:
                    hneeded = max(0, min(hneeded, y-1))
                    yhelp = y-hneeded
            else:  # y<0
                yhelp = max(0, scrh-hneeded-1)

            if x >= 0:
                if x+wneeded < scrw:
                    xhelp = x+1
                else:
                    wneeded = max(0, min(wneeded, x-1))
                    xhelp = x-wneeded
            else:  # x<0
                xhelp = max(0, scrh-wneeded-1)

            self.scr = vd.subwindow(scr, xhelp, yhelp, wneeded, hneeded)
            self.parentscr = scr

        self.scr.erase()
        self.scr.box()
        self.amgr.draw(self.scr, y=1, x=2, **kwargs)
        self.scr.refresh()


@VisiData.api
@functools.lru_cache(maxsize=None)
def getHelpPane(vd, name, module='visidata') -> HelpPane:
    ret = HelpPane(name)
    try:
        ret.amgr.load(name, (vd.pkg_resources_files(module)/f'ddw/{name}.ddw').open(encoding='utf-8'))
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
        module_path = vd.pkg_resources_files(__name__.split('.')[0])
        if os.system(' '.join(['man', str(module_path/'man/vd.1')])) != 0:
            vd.push(TextSheet('man_vd', source=module_path/'man/vd.txt'))


# in VisiData, g^H refers to the man page
BaseSheet.addCommand('g^H', 'sysopen-help', 'openManPage()', 'Show the UNIX man page for VisiData')
BaseSheet.addCommand('z^H', 'help-commands', 'vd.push(HelpSheet(name + "_commands", source=sheet, revbinds={}))', 'list commands and keybindings available on current sheet')
BaseSheet.addCommand('gz^H', 'help-commands-all', 'vd.push(HelpSheet("all_commands", source=None, revbinds={}))', 'list commands and keybindings for all sheet types')

BaseSheet.bindkey('F1', 'sysopen-help')
BaseSheet.bindkey('zF1', 'help-commands')
BaseSheet.bindkey('zBksp', 'help-commands')
BaseSheet.bindkey('gBksp', 'sysopen-help')

HelpSheet.addCommand(None, 'exec-command', 'quit(sheet); draw_all(); activeStack[0].execCommand(cursorRow.longname)', 'execute command on undersheet')
BaseSheet.addCommand(None, 'open-tutorial-visidata', 'launchBrowser("https://jsvine.github.io/intro-to-visidata/")', 'open https://jsvine.github.io/intro-to-visidata/')

vd.addMenuItem("Help", "VisiData tutorial", 'open-tutorial-visidata')
vd.addMenuItem("Help", 'Sheet commands', 'help-commands')
vd.addMenuItem("Help", 'All commands', 'help-commands-all')

vd.addGlobals(HelpSheet=HelpSheet)

vd.addMenuItems('''
    Help > Quick reference > sysopen-help
    Help > Command list > help-commands
''')
