from .vgit import *

def open_dir(p):
    if p.joinpath('.git').is_dir():
        vs = GitStatus(p)
        vs.gitBranchesSheet = GitBranches('branches', source=vs)
        vs.gitOptionsSheet = GitOptions('git-options', source=vs)
        vs.gitStashesSheet = GitStashes('stashes', source=vs)
        vs.gitRemotesSheet = GitRemotes('remotes', source=vs)
        return vs

    return DirSheet(p.name, source=p)

addGlobals(globals())
