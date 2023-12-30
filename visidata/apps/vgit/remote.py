from visidata import vd, VisiData, ItemColumn, AttrDict, RowColorizer, Path

from .gitsheet import GitSheet

@VisiData.api
def git_remote(vd, p, args):
    if not args or 'show' in args:
        return GitRemotes('remotes', source=p)


class GitRemotes(GitSheet):
    guide = '''
        # git remote
        Manage the set of repositories ("remotes") whose branches you track.

        - `a` to add a remote
        - `d` to mark a remote for deletion
        - `e` to edit the _remote_ or _url_
        - `z Ctrl+S` to commit the changes.
    '''
    rowtypes = 'remotes'  # rowdef: dict(remote=, url=, type=)
    columns=[
        ItemColumn('remote', setter=lambda c,r,v: c.sheet.set_remote(c,r,v)),
        ItemColumn('type'),
        ItemColumn('url', width=40, setter=lambda c,r,v: c.sheet.set_url(c,r,v)),
    ]
    nKeys = 1
    defer = True

    def set_remote(self, col, row, val):
        self.loggit('remote', 'rename', self.column('remote').getSourceValue(row), val)

    def set_url(self, col, row, val):
        self.loggit('remote', 'set-url', row.remote, val)

    def iterload(self):
        for line in self.git_lines('remote', '-v', 'show'):
            name, url, paren_type = line.split()
            yield AttrDict(remote=name, url=url, type=paren_type[1:-1])

    def commitDeleteRow(self, row):
        self.loggit('remote', 'remove', row.remote)

    def commitAddRow(self, row):
        row.remote = self.column('remote').getValue(row)
        row.url = self.column('url').getValue(row)
        self.loggit('remote', 'add', row.remote, row.url)

    def newRow(self):
        return AttrDict()


GitSheet.addCommand('', 'git-open-remotes', 'vd.push(git_remote(Path("."), ""))', 'open git remotes sheet')

vd.addMenuItems('''
    Git > Open > remotes > git-open-remotes
''')
