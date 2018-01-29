from visidata import *


def collapse_single_children(tree):
    # combine parents and only children

    if not isinstance(tree, dict):
        return tree

    value = dict()
    for k, v in tree.items():
        if isinstance(v, dict) and len(v) == 1:
            vKey = list(v.keys())[0]
            value[k + vKey] = collapse_single_children(v[vKey])
        else:
            value[k] = collapse_single_children(v)

    return value

def mkmenu(*cmdmaps):
    def rec_dd():
        return collections.defaultdict(rec_dd)

    cmdtree = rec_dd()
    for commands in cmdmaps:
      for cmd in commands.values():
         if cmd.longname and cmd.execstr not in commands:
            longname = cmd.longname
            parts = longname.split('-')
            cmdnode = cmdtree
            for p in parts[:-1]:
                cmdnode = cmdnode[p+'-']
            assert isinstance(cmdnode, collections.defaultdict), longname # parent cannot also be leaf
            if parts[-1] in cmdnode:
                assert cmdnode[parts[-1]] is cmd, (cmd.name, cmd.execstr, cmdnode[parts[-1]].name, cmdnode[parts[-1]].execstr) 
            cmdnode[parts[-1]] = cmd

    cmdtree = collapse_single_children(cmdtree)

    return cmdtree
