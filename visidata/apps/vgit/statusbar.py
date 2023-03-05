from .gitsheet import vd, GitSheet


GitSheet.options.disp_status_fmt = '{sheet.progressStatus}‹{sheet.branchStatus}› {sheet.name}| '

@GitSheet.property
def progressStatus(sheet):
    inp = sheet.gitInProgress()
    return ('[%s] ' % inp) if inp else ''


@GitSheet.property
def branchStatus(sheet):
    if hasattr(sheet.gitRootSheet, 'branch'):
        return '%s%s' % (sheet.rootSheet.branch, sheet.rootSheet.remotediff)
    return ''


@GitSheet.api
def gitInProgress(sheet):
    p = sheet.gitPath
    if not p:
        return 'no repo'
    if (p/'rebase-merge').exists() or (p/'rebase-apply/rebasing').exists():
        return 'rebasing'
    elif p/'rebase-apply'.exists():
        return 'applying'
    elif p/'CHERRY_PICK_HEAD'.exists():
        return 'cherry-picking'
    elif p/'MERGE_HEAD'.exists():
        return 'merging'
    elif p/'BISECT_LOG'.exists():
        return 'bisecting'
    return ''
