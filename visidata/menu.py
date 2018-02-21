from visidata import *

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
