import string
import random
from . import GitLogSheet
from visidata import *

def randomBranchName():
    return ''.join(string.ascii_lowercase[random.randint(0, 25)] for i in range(10))

@GitLogSheet.api
def amendPrevious(self, targethash):
    'amend targethash with current index, then rebase newer commits on top'

    prevBranch = self.git_all('rev-parse', '--symbolic-full-name', '--abbrev-ref', 'HEAD').strip()

    ret = self.git_all('commit', '-m', 'MERGE '+targethash) # commit index to viewed branch
    newChanges = self.git_all('rev-parse', 'HEAD').strip()

    ret += self.git_all('stash', 'save', '--keep-index') # stash everything else
    with GitUndo('stash', 'pop'):
        tmpBranch = randomBranchName()
        ret += self.git_all('checkout', '-b', tmpBranch) # create/switch to tmp branch
        with GitUndo('checkout', prevBranch), GitUndo('branch', '-D', tmpBranch):
            ret += self.git_all('reset', '--hard', targethash) # tmpbranch now at targethash
            ret += self.git_all('cherry-pick', '-n', newChanges)  # pick new change from original branch
            ret += self.git_all('commit', '--amend', '--no-edit')  # recommit to fix targethash (which will change)
            ret += self.git_all('rebase', '--onto', tmpBranch, 'HEAD@{1}', prevBranch)  # replay the rest

    return ret.splitlines()
