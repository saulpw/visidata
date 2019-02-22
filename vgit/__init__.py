from visidata import *

from .git import *
from .merge import GitMerge
from .blame import GitBlame, GitFileSheet
from .diff import *
from .status import *
from .repo import *
from .amend import *

def open_git(p):
    p.joinpath('.git').is_dir() or error("not a git directory")
    vs = GitStatus(p)
    vs.gitBranchesSheet = GitBranches('branches', source=vs)
    vs.gitOptionsSheet = GitOptions('git-options', source=vs)
    vs.gitStashesSheet = GitStashes('stashes', source=vs)
    vs.gitRemotesSheet = GitRemotes('remotes', source=vs)
    return vs

addGlobals(globals())
