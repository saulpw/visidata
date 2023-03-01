from visidata import vd, VisiData, ItemColumn, AttrDict, RowColorizer, Path

from .gitsheet import GitSheet

@VisiData.api
def git_remote(vd, *args, **kwargs):
        return GitRemote('remotes', source=Path('.'))


class GitRemote(GitSheet):
    help = '''
        # git remote
        Manage the set of repositories ("remotes") whose branches you track.
        - `
    '''
    rowtypes = 'remotes'
    columns=[
        ItemColumn('remote', setter=lambda c,r,v: c.sheet.git('remote', 'rename', r.remote, v)),
        ItemColumn('type'),
        ItemColumn('url', width=40, setter=lambda c,r,v: c.sheet.git('remote', 'set-url', r.remote, v)),
    ]
    nKeys = 1
    defer = True

    def iterload(self):
        for line in self.git_lines('remote', '-v', 'show'):
            name, url, paren_type = line.split()
            yield AttrDict(remote=name, url=url, type=paren_type[1:-1])

    def commitDeleteRow(self, row):
        self.loggit('remote', 'remove', row.remote)

    def commitAddRow(self, row):
        self.loggit('remote', 'add', row.remote, row.url)

    def newRow(self):
        return AttrDict()
