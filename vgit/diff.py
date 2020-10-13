from visidata import *
from .git import GitSheet

option('git_diff_algo', 'minimal', 'algorithm to use for git diff')

__all__ = ['DifferSheet', 'HunksSheet', 'HunkViewer', 'getCommitSheet', 'getStagedHunksSheet', 'getHunksSheet']


# one column per ref
# special refs are 'working' and 'index'
# diffs colored compared with the 'base' ref (initially first ref); base ref can be changed (1/2/3/...)
# a/r/c/d should work
def getDiffSheet(fn, *refs):
    'one column per ref'


# @@ -2,7 +2,7 @@ context
# returns leftstart, leftcount, rightstart, rightcount, context
def parseContextLine(line):
    def _parseStartCount(s):
        sc = s.split(',')
        if len(sc) == 2:
            return sc
        if len(sc) == 1:
            return sc[0], 1

    _, linenums, context = line.split('@@')
    leftlinenums, rightlinenums = linenums.split()
    leftstart, leftcount = _parseStartCount(leftlinenums[1:])
    rightstart, rightcount = _parseStartCount(rightlinenums[1:])
    return int(leftstart), int(leftcount), int(rightstart), int(rightcount), context


class DifferSheet(GitSheet):
    rowtype = 'lines' # rowdef:  list of refs (1 per source)
    def __init__(self, relfn, *refs, **kwargs):
        super().__init__(str(relfn)+"_diff", refs=refs, **kwargs)
        self.fn = str(relfn)
        self.basenum = 0
        self.columns = [
#                ColumnItem('linenum', 0)
        ]
        self.columns.extend([
            ColumnItem(name, i+1, width=self.windowWidth//len(refs)-1, refnum=i)
                for i, name in enumerate(refs)
        ])

    def findDiffRow(self, refnum, startidx, direction):
        idx = startidx+direction
        while idx >= 0 and idx < len(self.rows):
            r = self.rows[idx]
            if r[self.basenum+1] != r[refnum+1]:
                return idx
            idx += direction

        status('no next diff')
        return startidx

    def colorDiffRow(self, c, row, v):
        if not row:
            return
        baseval = row[self.basenum+1]
        for c in self.columns[1:]:
            v = c.getValue(row)
            if v != baseval:
                if baseval is None:
                    return 'green'  # addition
                elif v is None:
                    return 'red'  # deletion
                else:
                    return 'yellow'  # difference

    def insertLine(self, refnum, linenum, line):
        i = -1
        for i, row in enumerate(self.rows):
            if row[0] == linenum:
                if row[refnum+1] is None:
                    row[refnum+1] = line
                    return
                # else keep looking
            elif row[0] > linenum:
                break

        self.rows.insert(i, self.newRow(linenum, refnum, line))

    def newRow(self, linenum, refnum, line):
        r = [None] * (len(self.refs)+1)  # one for base linenum and one for each ref
        r[0] = linenum
        r[refnum+1] = line
        return r

    def git_diff(self, fn, *args):
        args = list(args) + ['--', fn]
        return self.git_lines('diff',
            '--patch',
            '--inter-hunk-context=2',
            '--find-renames',
            '--no-color',
            '--no-prefix',
            '--diff-algorithm=' + options.git_diff_algo,
            '-U999999',
            *args)


    def getDiffCmd(self, fn, base, ref):
        if ref == base:
            return None

        if base == 'index':
            if ref == 'working':
                return self.git_diff(fn)
            else:
                error('notimpl: index as diff base for ref')
        elif base == 'working':
            error('notimpl: working as diff base for ref')
        else:
            if ref == 'working':
                return self.git_diff(fn, base)
            elif ref == 'index':
                return self.git_diff(fn, '--cached', base)
            else:
                return self.git_diff(fn, base, ref)

    def reload(self):
        self.rows = []

        baseref = self.refs[self.basenum]
        for linenum, line in enumerate(self.git_lines('show', baseref+':'+self.fn)):
            self.addRow(self.newRow(linenum, self.basenum, line))

        for refnum, ref in enumerate(self.refs):
            cmd = self.getDiffCmd(self.fn, baseref, ref)
            if not cmd:
                continue

            patchlines = list(cmd)

            leftstart = 0
            for line in patchlines[3:]:  # diff without the patch headers
                if line.startswith('---'):
                    pass
                elif line.startswith('+++'):
                    pass
                elif line.startswith('@@'):
                    leftstart, leftcount, rightstart, rightcount, context = parseContextLine(line)
                    leftstart -= 1
                    remainder = 0
                else:
                    typech = line[0]
                    rest = line[1:]
                    if typech == '-':
                        remainder = 1
                    elif typech == '+':
                        self.insertLine(refnum, leftstart, rest)
                        leftstart += 1
                        remainder = 0
                    elif typech == ' ':
                        leftstart += remainder
                        remainder = 0
                        self.insertLine(refnum, leftstart, rest)
                        leftstart += 1
                    else:
                        status(line)
                        continue  # header


def getHunksSheet(parent, *files):
    return HunksSheet('hunks', 'diff',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *[gf.filename for gf in files], source=parent)

def getStagedHunksSheet(parent, *files):
    return HunksSheet('staged_hunks', 'diff', '--cached',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *[gf.filename for gf in files], source=parent)

def getCommitSheet(name, parent, *refids):
    return HunksSheet(name, 'show',
                  '--diff-algorithm=' + options.git_diff_algo,
                  '--patch',
                  '--inter-hunk-context=2', '-U1',
                  '--no-color',
                  '--no-prefix', *refids, source=parent)

# source is arguments to git()
class HunksSheet(GitSheet):
    columns = [
        ColumnItem('origfn', 0, width=0),
        ColumnItem('filename', 1),
        ColumnItem('context', 2),
        ColumnItem('leftlinenum', 3),
        ColumnItem('leftcount', 4),
        ColumnItem('rightlinenum', 5),
        ColumnItem('rightcount', 6),
    ]

    def __init__(self, name, *git_args, **kwargs):
        super().__init__(name, **kwargs)
        self.git_args = git_args

    def reload(self):
        def _parseStartCount(s):
            sc = s.split(',')
            if len(sc) == 2:
                return sc
            if len(sc) == 1:
                return sc[0], 1

        self.rows = []
        leftfn = ''
        rightfn = ''
        header_lines = None
        diff_started = False
        for line in self.git_lines(*self.git_args):
            if line.startswith('diff'):
                diff_started = True
                continue
            if not diff_started:
                continue

            if line.startswith('---'):
                header_lines = [line]  # new file
                leftfn = line[4:]
            elif line.startswith('+++'):
                header_lines.append(line)
                rightfn = line[4:]
            elif line.startswith('@@'):
                header_lines.append(line)
                _, linenums, context = line.split('@@')
                leftlinenums, rightlinenums = linenums.split()
                leftstart, leftcount = _parseStartCount(leftlinenums[1:])
                rightstart, rightcount = _parseStartCount(rightlinenums[1:])
                self.addRow((leftfn, rightfn, context, int(leftstart), int(leftcount), int(rightstart), int(rightcount), header_lines))
                header_lines = header_lines[:2]  # keep file context
            elif line[0] in ' +-':
                self.rows[-1][-1].append(line)

    def openRow(self, row):
        'open the diff for this hunk'
        return HunkViewer([row], source=self)


theme('color_git_hunk_add', 'green', 'color for added hunk lines')
theme('color_git_hunk_del', 'red', 'color for deleted hunk lines')
theme('color_git_hunk_diff', 'yellow', 'color for hunk diffs')

class HunkViewer(GitSheet):
    colorizers = [
            RowColorizer(4, 'color_git_hunk_add', lambda s,c,r,v: s.colorDiffRow(c, r, v) == 'green'),
            RowColorizer(4, 'color_git_hunk_del', lambda s,c,r,v: s.colorDiffRow(c, r, v) == 'red'),
            RowColorizer(4, 'color_git_hunk_diff', lambda s,c,r,v: s.colorDiffRow(c, r, v) == 'yellow'),
    ]

    def __init__(self, hunks, **kwargs):
        super().__init__('hunk', hunks=hunks, **kwargs)
        self.columns = [
            ColumnItem('1', 1, width=self.windowWidth//2-1),
            ColumnItem('2', 2, width=self.windowWidth//2-1),
        ]

    def reload(self):
        if not self.hunks:
            vd.remove(self)
            return

        fn, _, context, linenum, _, _, _, patchlines = self.hunks[0]
        self.name = '%s:%s' % (fn, linenum)
        self.rows = []
        nextDelIdx = None
        for line in patchlines[3:]:  # diff without the patch headers
            typech = line[0]
            line = line[1:]
            if typech == '-':
                self.addRow([typech, line, None])
                if nextDelIdx is None:
                    nextDelIdx = len(self.rows)-1
            elif typech == '+':
                if nextDelIdx is not None:
                    if nextDelIdx < len(self.rows):
                        self.rows[nextDelIdx][2] = line
                        nextDelIdx += 1
                        continue

                self.addRow([typech, None, line])
                nextDelIdx = None
            elif typech == ' ':
                self.addRow([typech, line, line])
                nextDelIdx = None
            else:
                continue  # header

    def colorDiffRow(self, c, row, v):
        if row and row[1] != row[2]:
            if row[1] is None:
                return 'green'  # addition
            elif row[2] is None:
                return 'red'  # deletion
            else:
                return 'yellow'  # difference


HunkViewer.addCommand('2', 'git-apply-hunk', 'source.git_apply(hunks.pop(0), "--cached"); reload()', 'apply this hunk to the index and move to the next hunk'),
#HunkViewer.addCommand('1', 'git-remove-hunk', 'git_apply(hunks.pop(0), "--reverse")', 'remove this hunk from the diff'),
HunkViewer.addCommand(ENTER, 'git-skip-hunk', 'hunks.pop(0); reload()', 'move to the next hunk without applying this hunk'),
HunkViewer.addCommand('d', 'delete-line', 'source[7].pop(cursorRow[3]); reload()', 'delete a line from the patch'),

HunksSheet.addCommand('g^J', 'git-diff-selected', 'vd.push(HunkViewer(selectedRows or rows, source=sheet))', 'view the diffs for the selected hunks (or all hunks)'),
HunksSheet.addCommand('V', 'git-view-patch', 'vd.push(TextSheet("diff", source="\\n".join(cursorRow[7])))', 'view the raw patch for this hunk'),
#HunksSheet.addCommand('gV', 'git-view-patch-selected', '', 'view the raw patch for selected/all hunks'),
HunksSheet.addCommand('a', 'git-apply-hunk', 'git_apply(cursorRow, "--cached")', 'apply this hunk to the index'),
#HunksSheet.addCommand('r', 'git-reverse-hunk', 'git_apply(cursorRow, "--reverse")', 'undo this hunk'),
#HunksSheet.bindkey('d', 'git-reverse-hunk')

DifferSheet.addCommand('[', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, -1)', 'go to previous diff'),
DifferSheet.addCommand(']', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, +1)', 'go to next diff'),
DifferSheet.addCommand('za', '', 'add this line to the index'),
