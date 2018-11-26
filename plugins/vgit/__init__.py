from .vgit import *

def open_dir(p):
    if p.joinpath('.git').is_dir():
        return GitStatus(p)
    return DirSheet(p.name, source=p)

addGlobals(globals())
