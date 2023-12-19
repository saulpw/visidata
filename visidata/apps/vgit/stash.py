from visidata import vd, VisiData, ItemColumn, AttrDict


from .gitsheet import GitSheet
from .diff import GitDiffSheet


@VisiData.api
def git_stash(vd, p, args):
    if 'list' in args:
        return GitStashes('git-stash-list', source=p, gitargs=args)


class GitStashes(GitSheet):
    guide = '''
        # git stash
        This is the list of changes that have been stashed previously.

        `a` to apply this stashed change (without removing it)
        `d` to drop this stashed change
        `b` to create a branch from this stashed change'),
    '''
    rowtype = 'stashed change'  # rowdef: AttrDict(stashid=, branched_from=, sha1=, msg=)
    columns = [
        ItemColumn('stashid'),
        ItemColumn('branched_from'),
        ItemColumn('sha1'),
        ItemColumn('msg'),
        ItemColumn('line', width=0),
    ]

    def iterload(self):
        for line in self.git_lines('stash', *self.gitargs):
            stashid, ctx, rest = line.split(': ', 2)
            if ctx.startswith('WIP on '):
                branched_from = ctx[len('WIP on '):]
                sha1, msg = rest.split(' ', 1)
            elif ctx.startswith('On '):
                branched_from = ctx[len('On '):]
                sha1 = ''
                msg = rest
            yield AttrDict(
                line=line,
                stashid=stashid,
                branched_from=branched_from,
                sha1=sha1,
                msg=msg.strip(),
            )

    def openRow(self, row):
        'open this stashed change'
        return GitDiffSheet(row.stashid, "diffs", gitargs=['stash show --no-color --patch', row.stashid], source=self.source)


GitSheet.addCommand('', 'git-open-stashes', 'vd.push(git_stash(source, ["list"]))', 'push stashes sheet')

GitStashes.addCommand('a', 'git-stash-apply', 'loggit("stash", "apply", cursorRow[0])', 'apply this stashed change without removing')
GitStashes.addCommand('', 'git-stash-pop', 'loggit("stash", "pop", cursorRow[0])', 'apply this stashed change and drop it')
GitStashes.addCommand('d', 'git-stash-drop', 'loggit("stash", "drop", cursorRow[0])', 'drop this stashed change')
GitStashes.addCommand('b', 'git-stash-branch', 'loggit("stash", "branch", input("create branch from stash named: "), cursorRow[0])', 'create branch from stash')


vd.addMenuItems('''
    Git > Open > stashes > git-open-stashes
    Git > Stash > apply > git-stash-apply
    Git > Stash > drop > git-stash-drop
    Git > Stash > apply then drop  > git-stash-pop
    Git > Stash > create branch > git-stash-branch
''')
