
from vdtui import *
from git import GitSheet

# show this particular code block in remote/HEAD/index/working

# toggle show whole file, and diffs with context
## when showing whole file, how to align lines

# keystrokes:
#        '1'=remote   Revert HEAD chunk in index; working should stay same
#    'r'/'2'=HEAD     Unstage anything in index; working should stay same
#  ENTER/'3'=index    No action; move to next chunk/file
#    'a'/'4'=working  Stage chunk to index.
#    'd'              remove hunk from working dir

#  - nothing should change the working copy except 'd'.
#  - 1/2/3/4 are 'safe' and only affect the index.
#     a) If e.g. changes are in working (and nothing in index)
#     b) '4' stages them
#     c) if '1' stages a grand reversion of everything local
#     d) then '4' should bring the index back to the same exact state as after (b)

def _parseStartCount(s):
    sc = s.split(',')
    if len(sc) == 2: return sc
    if len(sc) == 1: return sc[0], 1


class GitHunk:
    def __init__(self, fn, left, right, hunkdef):
        self.fn = left
        self.left = left
        self.right = right
        self.hunkdef = hunkdef
        self.difflines = []

        _, linenums, self.context = hunkdef.split('@@')
        leftlinenums, rightlinenums = linenums.split()
        leftstart, leftcount = _parseStartCount(leftlinenums[1:])
        rightstart, rightcount = _parseStartCount(rightlinenums[1:])
        self.leftstart, self.leftcount = int(leftstart), int(leftcount)
        self.rightstart, self.rightcount = int(rightstart), int(rightcount)

def parseDiff(left, right, lines):
    diff_started = False
    files = {}   # '-'/'+': (fn, timestamp)
    gh = None  # current GitHunk

    for line in lines:
        if line.startswith('diff'):
            diff_started = True
            continue
        elif line.startswith('index'):
            # save off refs?
            continue

        if not diff_started:
            continue

        if line.startswith('---'):
            files['-'] = line[4:].split(maxsplit=1)
        elif line.startswith('+++'):
            files['+'] = line[4:].split(maxsplit=1)
        elif line.startswith('@@'):  # new hunk
            if gh:
                yield gh
            gh = GitHunk(files['+'][0], left, right, line)
        elif line[0] in ' +-':
            gh.difflines.append(line)
        else:
            status(line)

# generates leftlinenum, rightlinenum, leftline, rightline
def parseHunk(gh):
    linePairs = []
    nextDelIdx = None
    leftlinenum = gh.leftstart
    rightlinenum = gh.rightstart  # start of linePairs

    for line in gh.difflines:
        typech = line[0]
        line = line[1:]
        if typech == ' ':
            for a, b in linePairs:
                r = [None, None, a, b]
                if a:
                    leftlinenum += 1
                    r[0] = leftlinenum
                if b:
                    rightlinenum += 1
                    r[1] = rightlinenum
                yield r

            leftlinenum += 1
            rightlinenum += 1
            yield (leftlinenum, rightlinenum, line, line)
            nextDelIdx = None
            linePairs = []
        elif typech == '-':
            if nextDelIdx is None:
                assert not linePairs
                nextDelIdx = 0
            linePairs.append([line, None])
        elif typech == '+':
            if nextDelIdx is not None:
                if nextDelIdx < len(linePairs):
                    linePairs[nextDelIdx][1] = line
                    nextDelIdx += 1
                    continue
            leftlinenum += 0.0001
            rightlinenum += 1
            yield leftlinenum, rightlinenum, None, line
            nextDelIdx = None

    for a, b in linePairs:
        r = [None, None, a, b]
        if a:
            leftlinenum += 1
            r[0] = leftlinenum
        if b:
            rightlinenum += 1
            r[1] = rightlinenum
        yield r

class GitMerge(GitSheet):
    def __init__(self, gf):
        super().__init__(str(gf)+'_merge', gf)
        self.columns = [
            Column('#:HEAD', getter=lambda r: r[0]),
            Column('#:index', getter=lambda r: r[1]),
            Column('#:working', getter=lambda r: r[2]),
            Column('1:HEAD', getter=lambda r: r[3]),
            Column('2:index', getter=lambda r: r[4]),
            Column('3:working', getter=lambda r: r[5]),
        ]

#        self.addColorizer('col', 4, lambda s,c,r,v: 'green' if c is s.columns[2] else None)
#        self.addColorizer('cell', 5, self.colorDiffCell)

    # green for index cells not in HEAD; or working cells not in index
    # yellow for lines with content differing in both
    # red for index cells not in working; or HEAD cells not in index
    @staticmethod
    def colorDiffCell(sheet, col, row, val):
        if col is sheet.columns[2]: # index
            if row[1] is None:     # index not in HEAD
                return 'green'
            elif row[3] is None:   # index not in working
                return 'red'
            elif row[2] != row[1] or row[2] != row[3]:
                return 'yellow'
        elif col is sheet.columns[3]:  # working
            if row[2] is None:     # working not in index
                return 'green'
            elif row[3] != row[2]:
                return 'yellow'
        elif col is sheet.columns[1]:
            if row[2] is None:     # HEAD not in index
                return 'red'
            elif row[2] != row[1]:
                return 'yellow'

    def reload(self):
        def _getIndex(rows, srcnum, linenum):
            for i, r in enumerate(rows):
                assert r[srcnum] is not None
                if r[srcnum] == linenum:
                    return i
                elif r[srcnum] > linenum:
                    break

            r = [None, None, None, None, None, None]
            r[srcnum] = linenum
            rows.insert(i, r)
            return i

        fn = self.source.filename

        self.rows = []
        for i, line in enumerate(git_lines('show', 'HEAD:' + fn)):
            self.rows.append([i+1, None, None, line, None, None])

        for gh in parseDiff(0, 1, git_lines('diff', '--patch', '--cached', '--no-color', '--no-prefix', fn)):
#            a = _getIndex(self.rows, gh.left, gh.leftstart)
#            b = _getIndex(self.rows, gh.left, gh.leftstart + gh.leftcount)
            for leftlinenum, rightlinenum, leftline, rightline in parseHunk(gh):
                r = self.rows[_getIndex(self.rows, gh.left, leftlinenum)]
                r[gh.right] = rightlinenum
                r[gh.right+3] = rightline
                assert r[gh.left+3] == leftline, (r[gh.left+3], leftline)

#        parseDiff(1, 2, git_lines('diff', '--patch', '--no-color', '--no-prefix', fn)))
        '''
        for gh in hunks:
            for i in range(lastLines[gh.left], gh.leftstart):



            lastLines[gh.left] = gh.leftstart + gh.leftcount

            for leftline, rightline, left, right in parseHunk(gh):
                rowIdx = _getIndex(self.rows, gh.left, leftline)

                if r[gh.left] is not None:
                    assert r[gh.left] == left, (gh.left, r[gh.left], left)
                if r[gh.right] is not None:
                    assert r[gh.right] == right, (gh.right, r[gh.right], right)
                r[gh.left] = left
                r[gh.right] = right
'''

    def reload1(self):
        fn = self.source.filename

        # every column is that compared with index
        head = list(line for line in git_lines('show', 'HEAD:' + fn))
        index = list(line for line in git_lines('show', ':' + fn))
        working = list(line[:-1] for line in self.source.path.open_text())
        remote = head

        allFiles = [remote, head, index, working]
        allIndexes = [0,0,0,0]

        # get all relevant diffs
        # sort GitHunks by fn, startline
        # until next startline, append rows from each file verbatim (no changes)

        # diff of index and working
        allHunks = list(parseDiff(2, 3, git_lines('diff', '--patch', '--no-color', '--no-prefix', fn)))
        lineIndexes = {}  # [(1/2/3, linenum)] -> 
        for gh in sorted(allHunks, key=lambda gh: (gh.fn, min(gh.leftstart, gh.rightstart))):
            while allIndexes[gh.left] < gh.leftstart-1 or allIndexes[gh.right] < gh.rightstart-1:
                # add context lines before this hunk starts
                r = [None] * len(allFiles)
                self.rows.append(r)
                if allIndexes[gh.left] < gh.leftstart-1:
                    r[gh.left] = allFiles[gh.left][allIndexes[gh.left]]
                    allIndexes[gh.left] += 1
                if allIndexes[gh.right] < gh.rightstart-1:
                    r[gh.right] = allFiles[gh.right][allIndexes[gh.right]]
                    allIndexes[gh.right] += 1

            hunklines = list(parseHunk(gh))
            for left, right in hunklines:
                r = [None] * len(allFiles)
                self.rows.append(r)
                r[gh.left] = left
                r[gh.right] = right

            allIndexes[gh.left] += gh.leftcount
            allIndexes[gh.right] += gh.rightcount

