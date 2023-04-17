from visidata import vd, Menu
from .gitsheet import GitSheet


@GitSheet.api
def abortWhatever(sheet):
    inp = sheet.gitInProgress()
    if inp.startswith('cherry-pick'):
        sheet.modifyGit('cherry-pick', '--abort')
    elif inp.startswith('merg'):
        sheet.modifyGit('merge', '--abort')
    elif inp.startswith('bisect'):
        sheet.modifyGit('bisect', 'reset')
    elif inp.startswith('rebas') or inp.startswith('apply'):
        sheet.modifyGit('rebase', '--abort')  # or --quit?
    else:
        vd.status('nothing to abort')


GitSheet.addCommand('^A', 'git-abort', 'abortWhatever()', 'abort the current in-progress action')


vd.addMenuItems('Git > Abort > git-abort')
