from visidata import *

globalCommand(' ', 'cmd=choose(mkmenu(*_commands.maps), cmdhelp, sheet); cmd and exec_command(cmd, keystrokes=cmd.longname)', 'start menu command')

option('color_menu_prefix', 'green', 'color of accepted menu part')
option('color_menu_option', 'white', 'default menu color')
option('color_menu_cursor', 'bold reverse', 'color of menu cursor')
option('color_menu_help', 'bold', 'color of menu help text')
option('disp_menu_helpfmt', '{bindings} ⇨ {helpstr}', 'string between command keybindings and helpstr in menu') # ⇢ ⇒ → ↠
option('disp_menu_helpsep', ' | ', 'string between submenu options')


commandMenu = collections.OrderedDict()

def menu(parentname, itemorder):
    m = commandMenu
    for name in parentname.split('-'):
        if not name:
            break
        name += '-'
        if name not in m:
            m[name] = collections.OrderedDict()
        m = m[name]

    for item in itemorder.split():
        if item not in m:
            if item.endswith('-'):
                m[item] = collections.OrderedDict()
            else:
                m[item] = ''

menu('', 'sheet- column- rows- modify- data- meta- info- python- view-')
menu('sheet-', 'new open- reload duplicate- freeze save quit-')
menu('column-', 'name- hide width- type- key- aggregator- freeze cache-')
menu('rows-', 'select- toggle- unselect- sort-')
menu('modify-', 'add- edit- move- clear- fill- delete- set-column-')
menu('data-', 'clipboard- plot- aggregate- describe melt pivot')
menu('meta-', 'sheets columns- options cmdlog- replay- threads-')
menu('info-', 'errors- manpage sheet version')
menu('python-', 'eval- exec push-')
menu('view-', 'find- go- scroll-')


def collapse_single_children(tree):
    # combine parents and only children

    if not isinstance(tree, dict):
        return tree

    value = collections.OrderedDict()
    for k, v in tree.items():
        if isinstance(v, dict) and len(v) == 1:
            vKey = list(v.keys())[0]
            value[k + vKey] = collapse_single_children(v[vKey])
        else:
            value[k] = collapse_single_children(v)

    return value


def mkmenu(*cmdmaps):
    cmdtree = deepcopy(commandMenu)
    for commands in cmdmaps:
        for cmd in commands.values():
            if isinstance(cmd, Command):
                if cmd.longname and cmd.execstr not in commands:
                    longname = cmd.longname
                    parts = longname.split('-')
                    cmdnode = cmdtree
                    for p in parts[:-1]:
                        p += '-'
                        if p not in cmdnode:
                            cmdnode[p] = collections.OrderedDict()
                        cmdnode = cmdnode[p]
                    assert isinstance(cmdnode, collections.OrderedDict), longname # parent cannot also be leaf
                    cmdnode[parts[-1]] = cmd

    cmdtree = collapse_single_children(cmdtree)

    return cmdtree

def cmdhelp(cmdname, sheet):
    cmd = sheet.getCommand(cmdname)
    if not cmd:
        return None

    helpstr = getattr(cmd, 'helpstr', '')
    helpstr = helpstr.replace("current cell", '[%s]' % clipstr(sheet.cursorDisplay, 10)[0])
    helpstr = helpstr.replace("current column", '[%s]' % sheet.cursorCol.name)
    selrowstr = "selected rows"
    if sheet._selectedRows:
        selrowstr = "%s selected rows" % len(sheet._selectedRows)
    else:
        if "selectedRows or rows" in cmd.execstr:
            selrowstr = "all %s rows" % len(sheet.rows)
        else:
            selrowstr = "[no rows selected]" # will have no effect
    helpstr = helpstr.replace("selected rows", selrowstr)
    helpstr = helpstr.replace("rows", '[%s]' % sheet.rowtype)

    # get all keybindings to cmdname
    bindings = set()
    for cmd in sheet._commands.values():
        othercmd = sheet.getCommand(cmd.name)
        if othercmd and othercmd.longname == cmdname and cmd.name != cmdname:
            bindings.add(cmd.name)

    bindings = ' '.join(bindings)
    return options.disp_menu_helpfmt.format(**locals())

def cmdsort(cmds):
    return list(cmds.keys())


def choose(cmdtree, helpfunc=None, sheet=None):
    '''`cmdtree` is dict of str to nested dict or leaf. Returns leaf, or None, or raises Exception.
    helpfunc(cmdname, sheet) should return a helpstr for the given cmdname (composed from the cmdtree)'''
    vdobj = vd()
    scr = vdobj.scr
    sheet = sheet or vdobj.sheets[0]

    v = vd().callHook('preedit')
    if v and v[0]:
        for part in v[0].split('-'):
            if part+'-' in cmdtree:
                cmdtree = cmdtree[part+'-']
            else:
                cmdtree = cmdtree[part]
                break
        return cmdtree

    cmdpath = [[cmdtree, 0]]
    while cmdpath:
        curlevel = cmdpath[-1]
        curnode, curidx = curlevel

        if not isinstance(curnode, dict): # leaf node
            longname = ''.join(cmdsort(n)[i] for n,i in cmdpath[:-1])
            vd().callHook('postedit', longname)
            return curnode

        menuy = vdobj.windowHeight-1
        helpy = vdobj.windowHeight-2
        width = vdobj.windowWidth
        sheet.draw(scr)
        lstatus = vdobj.drawLeftStatus(scr, sheet)
        menux = len(lstatus)+2

        rstatus = vdobj.drawRightStatus(scr, sheet)
        scr.addstr(helpy, 0, ' '*width, 0)

        # curnode[cmdkeys[curidx]] is the entry (dict or leaf)
        cmdkeys = cmdsort(curnode) or error('nothing to choose from')

        # fix topmost cursor
        if curidx < 0: curidx = curlevel[1] = 0
        elif curidx >= len(cmdkeys): curidx = curlevel[1] = len(cmdkeys)-1

        maxitemwidth = max(len(x) for x in cmdkeys)+2
        menuwidth = width - menux - len(rstatus) - 2
        nVisibleItems = menuwidth//maxitemwidth
        nItems = len(cmdkeys)
        leftidx = 0
        if nItems > nVisibleItems:
            middleidx = nVisibleItems//2
            leftidx = max(curidx - middleidx, 0)

        scr.addstr(menuy, menux, ' '*menuwidth, 0)

        # draw the currently selected path on the left
        regattr = colors[options.color_menu_prefix]
        for cmdnode, cmdidx in cmdpath[:-1]:
            s = cmdsort(cmdnode)[cmdidx]
            clipdraw(scr, helpy, menux, s, regattr, len(s))
            menux += len(s)

        # then the options under the latest node
        for i in range(leftidx, len(cmdkeys)):
            k = cmdkeys[i]
            k = ' '*((maxitemwidth-len(k))//2) + k
            attr = colors[options.color_menu_option]
            if i == curidx:
                attr, attrpre = colors.update(attr, 0, options.color_menu_cursor, 9)
                curx = menux

            clipdraw(scr, menuy, menux, k, attr, maxitemwidth) # min(width-len(rstatus)-menux, len(k)))
            menux += maxitemwidth
            if menux > width-len(rstatus):
                break

        # display helpstr for cursor command
        curcmd = ''.join(cmdsort(n)[i] for n, i in cmdpath)
        if helpfunc:
            try:
                helpstr = helpfunc(curcmd, sheet)
            except Exception as e:
                helpstr = str(e)
            submenu = curnode[cmdkeys[curidx]]
            if not helpstr and isinstance(submenu, dict):
                helpstr = options.disp_menu_helpsep.join(cmdsort(submenu))
            if helpstr:
                helpx = max(width-len(helpstr)-2, 0)
                clipdraw(scr, helpy, helpx, helpstr, colors[options.color_menu_help])
        else:
            helpstr = curnode[cmdkeys[curidx]].__doc__

        ch = vdobj.getkeystroke(scr, sheet)
        if not ch: continue
        elif ch in ['ESC', '^C', '^Q']:             raise EscapeException(ch)
        elif ch in ['k', '^A', 'KEY_HOME']:         curlevel[1] = 0
        elif ch in ['h', '^B', 'KEY_LEFT']:         curlevel[1] -= 1
        elif ch in ['j', '^E', 'KEY_END']:          curlevel[1] = len(cmdkeys)-1
        elif ch in ['l', '^F', 'KEY_RIGHT']:        curlevel[1] += 1
        elif ch in ['^I', ENTER, ' ', '-']:         cmdpath.append([curnode[cmdkeys[curidx]], 0]);
        elif ch in ['q', 'KEY_BACKSPACE']:          cmdpath = cmdpath[:-1];
        else:
            pass
