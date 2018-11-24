from vdtui import *
from git import GitSheet

option('diff_algorithm', 'minimal')


# one column per ref
# special refs are 'working' and 'index'
# diffs colored compared with the 'base' ref (initially first ref); base ref can be changed (1/2/3/...)
# a/r/c/d should work
def getDiffSheet(fn, *refs):
    'one column per ref'


def git_diff(fn, *args):
    args = args + ['--', fn]
    return git_lines('diff',
            '--patch',
            '--inter-hunk-context=2',
            '--find-renames',
            '--no-color',
            '--no-prefix',
            '--diff-algorithm=' + options.diff_algorithm,
            '-U999999',
            *args)


def getDiffCmd(fn, base, ref):
    if ref == base:
        return None

    if base == 'index':
        if ref == 'working':
            return git_diff(fn)
        else:
            error('notimpl: index as diff base for ref')
    elif base == 'working':
        error('notimpl: working as diff base for ref')
    else:
        if ref == 'working':
            return git_diff(fn, base)
        elif ref == 'index':
            return git_diff(fn, '--cached', base)
        else:
            return git_diff(fn, base, ref)


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
    commands = [
        Command('[', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, -1)', 'go to previous diff'),
        Command(']', 'cursorRowIndex = findDiffRow(cursorCol.refnum, cursorRowIndex, +1)', 'go to next diff'),
        Command('za', '', 'add this line to the index'),
    ]
    def __init__(self, relfn, *refs):
        super().__init__(str(relfn)+"_diff", *refs)
        self.fn = str(relfn)
        self.basenum = 0
        self.columns = [
#                ColumnItem('linenum', 0)
        ]
        self.columns.extend([
            ColumnItem(name, i+1, width=vd().windowWidth//len(refs)-1, refnum=i)
                for i, name in enumerate(refs)
        ])
        self.addColorizer(Colorizer('row', 4, DifferSheet.colorDiffRow))

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
        r = [None] * (len(self.sources)+1)  # one for base linenum and one for each ref
        r[0] = linenum
        r[refnum+1] = line
        return r

    def reload(self):
        self.rows = []

        baseref = self.sources[self.basenum]
        for linenum, line in enumerate(git_lines('show', baseref+':'+self.fn)):
            self.rows.append(self.newRow(linenum, self.basenum, line))

        for refnum, ref in enumerate(self.sources):
            cmd = getDiffCmd(self.fn, baseref, ref)
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


addGlobals(globals())
