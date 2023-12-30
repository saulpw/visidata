from visidata import vd, VisiData, ItemColumn, RowColorizer, AttrDict, Column

from .gitsheet import GitSheet

vd.option('git_diff_algo', 'minimal', 'algorithm to use for git diff')
vd.theme_option('color_git_hunk_add', 'green', 'color for added hunk lines')
vd.theme_option('color_git_hunk_del', 'red', 'color for deleted hunk lines')
vd.theme_option('color_git_hunk_diff', 'yellow', 'color for hunk diffs')

@VisiData.api
def git_diff(vd, p, args):
    return GitDiffSheet('git-diff', source=p, gitargs=args)

def _parseStartCount(s):
    sc = s.split(',')
    if len(sc) == 2:
        return sc
    if len(sc) == 1:
        return sc[0], 1


class GitDiffSheet(GitSheet):
    columns = [
        ItemColumn('a_fn', width=0),
        ItemColumn('fn', 'b_fn', width=30, hoffset=-28),
        ItemColumn('a_lineno', type=int, width=0),
        ItemColumn('lineno', 'b_lineno', type=int, width=8),
        Column('count', width=10, getter=lambda c,r: c.sheet.hunkCount(r)),
        ItemColumn('context'),
        ItemColumn('lines', type=''.join),
    ]

    guide = '''# {sheet.cursorRow.a_fn}
{sheet.cursorLines}'''

    def hunkCount(self, row):
        return f'-{row.a_count}/+{row.b_count}'

    @property
    def cursorLines(self):
        r = ''
        for line in self.cursorRow.lines[2:]:
            if line.startswith('-'):
                line = '[:git_hunk_del]' + line + '[/]'
            elif line.startswith('+'):
                line = '[:git_hunk_add]' + line + '[/]'

            r += line + '\n'
        r = r[4:]
        return r

    def iterload(self):
        current_hunk = None

        for line in self.git_lines('diff --patch --inter-hunk-context=2 --find-renames --no-color --no-prefix', *self.gitargs):
            if line.startswith('diff'):
                diff_started = True
                continue
            if not diff_started:
                continue

            if line.startswith('---'):
                hunk_lines = [line]  # new file
                leftfn = line[4:]
            elif line.startswith('+++'):
                hunk_lines.append(line)
                rightfn = line[4:]
            elif line.startswith('@@'):
                hunk_lines.append(line)
                _, linenums, context = line.split('@@')
                leftlinenums, rightlinenums = linenums.split()
                leftstart, leftcount = _parseStartCount(leftlinenums[1:])
                rightstart, rightcount = _parseStartCount(rightlinenums[1:])
                current_hunk = AttrDict(
                    a_fn=leftfn,
                    b_fn=rightfn,
                    context=context,
                    a_lineno=int(leftstart),
                    a_count=0,
                    b_lineno=int(rightstart),
                    b_count=0,
                    lines=hunk_lines
                )
                yield current_hunk
                hunk_lines = hunk_lines[:2]  # keep file context only

            elif line[0] in ' +-':
                current_hunk.lines.append(line)
                if line[0] == '+':
                    current_hunk.a_count += 1
                elif line[0] == '-':
                    current_hunk.b_count += 1

    def openRow(self, row):
        return HunkViewer(f'{row.a_fn}:{row.a_lineno}', source=self.source, hunks=[row])


class HunkViewer(GitSheet):
    colorizers = [
        RowColorizer(4, 'color_git_hunk_add', lambda s,c,r,v: r and r.old != r.new and r.old is None),
        RowColorizer(4, 'color_git_hunk_del', lambda s,c,r,v: r and r.old != r.new and r.new is None),
        RowColorizer(5, 'color_git_hunk_diff', lambda s,c,r,v: r and r.old != r.new and r.new is not None and r.old is not None),
    ]
    columns = [
        ItemColumn('1', 'old', width=40),
        ItemColumn('2', 'new', width=40),
    ]

    def draw(self, scr):
        self.column('1').width=self.windowWidth//2-1
        self.column('2').width=self.windowWidth//2-1
        super().draw(scr)

    def iterload(self):
        nextDelIdx = None
        for hunk in self.hunks:
          for line in hunk.lines[3:]:  # diff without the patch headers
            typech = line[0]
            line = line[1:]
            if typech == '-':  # deleted
                yield AttrDict(hunk=hunk, type=typech, old=line)
                if nextDelIdx is None:
                    nextDelIdx = len(self.rows)-1
            elif typech == '+':  # added
                if nextDelIdx is not None:
                    if nextDelIdx < len(self.rows):
                        self.rows[nextDelIdx].new = line
                        nextDelIdx += 1
                        continue

                yield AttrDict(hunk=hunk, type=typech, new=line)
                nextDelIdx = None
            elif typech == ' ':  # unchanged
                yield AttrDict(hunk=hunk, type=typech, old=line, new=line)
                nextDelIdx = None
            else:
                continue  # header


HunkViewer.addCommand('2', 'git-apply-hunk', 'source.git_apply(cursorRow.hunk, "--cached"); reload()', 'apply this hunk to the index and move to the next hunk')
HunkViewer.addCommand('1', 'git-remove-hunk', 'source.git_apply(cursorRow.hunk, "--reverse"); reload()', 'remove this hunk from staging')
HunkViewer.addCommand('Enter', 'git-skip-hunk', 'hunks.pop(0); reload()', 'move to the next hunk without applying this hunk')
HunkViewer.addCommand('d', 'delete-line', 'source[7].pop(cursorRow[3]); reload()', 'delete a line from the patch')

#HunksSheet.addCommand('g^J', 'git-diff-selected', 'vd.push(HunkViewer(selectedRows or rows, source=sheet))', 'view the diffs for the selected hunks (or all hunks)')

@GitDiffSheet.api
def git_apply(sheet, row, *args):
    sheet.git('apply -p0 -', *args, _in='\n'.join(row.lines)+'\n')

    c = sheet.hunkCount(row)
    vd.status(f'applied hunk ({c})')
    sheet.reload()


#DiffSheet.addCommand('[', '', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, -1)', 'go to previous diff')
#DiffSheet.addCommand(']', '', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, +1)', 'go to next diff')

GitDiffSheet.addCommand('a', 'git-add-hunk', 'git_apply(cursorRow, "--cached")', 'apply this hunk to the index')

vd.addMenuItems('''
    Git > Stage > current hunk > git-add-hunk
    Git > Stage > current hunk > git-add-hunk
''')

vd.addGlobals(
    GitDiffSheet=GitDiffSheet,
    HunkViewer=HunkViewer
)
