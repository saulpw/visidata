from itertools import islice

from visidata import vd, Column, VisiData, ItemColumn, AttrColumn, Path, AttrDict

from .gitsheet import GitSheet


CONFIG_CONTEXTS = ('local', 'global', 'system')

@VisiData.api
def git_config(vd, p, args):
    if not args or '-l' in args:
        return GitConfig('git-config', source=p)

vd.git_options = vd.git_config

def batched(iterable, n=1):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    assert n >= 1, 'n must be at least one'

    while (batch := tuple(islice(iter(iterable), n))):
        yield batch


class GitConfigColumn(Column):
    def calcValue(self, row):
        return row.get(self.expr)

    def putValue(self, row, val):
        if val is None:
            self.sheet.loggit('config', '--unset', '--'+self.expr, row['option'])
        else:
            self.sheet.loggit('config', '--'+self.expr, row['option'], val)

        row[self.expr] = val


class GitConfig(GitSheet):
    guide = '''
        # git config
        Add, edit, or delete git config options.

        - Make changes using standard commands like `a`dd and `e`dit
        - `z Ctrl+S` to commit changes to git config file.
    '''
    rowtype = 'git options'  # rowdef: [scope, origin, opt, val]
    defer = True
    columns = [
        ItemColumn('option', width=20),
    ]
    nKeys = 1

    def iterload(self):
        cmd = self.git_iter('config', '--list', '--show-scope', '--show-origin', '-z')
        self.gitopts = {}
        scopes = {c.name:c for c in self.columns}
        for row in batched(cmd, 3):
            if len(row) < 3:
                break

            scope, origin, optval = row
            opt, val = optval.split('\n', 1)

            if opt in self.gitopts:
                r = self.gitopts[opt]
            else:
                r = AttrDict(option=opt)
                self.gitopts[opt] = r
                yield r

            r[scope] = val

            if scope not in scopes:
                c = GitConfigColumn(scope, expr=scope)
                self.addColumn(c)
                scopes[scope] = c

    def commitDeleteRow(self, row):
        for k in CONFIG_CONTEXTS:
            if row.get(k):
                self.loggit('config', '--unset', '--'+k, row['option'])

    def commitAddRow(self, row):
        for k in CONFIG_CONTEXTS:
            if row.get(k):
                self.loggit('config', '--add', '--'+k, row['option'], row.get(k))


GitSheet.addCommand('gO', 'git-config', 'vd.push(GitConfig("git_config", source=Path(".")))', 'push sheet of git options')


vd.addMenuItems('''
    Git > Config > git-config
''')
