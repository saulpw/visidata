
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


class GitMerge(GitSheet):
    columns = [
            Column('1/remote', width=10, getter=lambda r: r[0][1]),
            Column('2/HEAD', getter=lambda r: r[1][1]),
            Column('3/index', getter=lambda r: r[2][1]),
            Column('4/working', getter=lambda r: r[3][1]),
    ]

    def __init__(self, gf):
        super().__init__(str(gf)+'_merge', gf)
        self.addColorizer(Colorizer('cell', 5, self.colorDiffCell))
#        Colorizer('col', 4, lambda s,c,r,v: 'green' if c is s.columns[2] else None)

    @staticmethod
    def colorDiffCell(sheet, col, row, val):
        if val != row[1][1]:       # diff from HEAD
            if val == row[2][1]:   # but same as index
                return 'green'  #   will be committed
            else:
                return 'red'    # changed and not in index

    def reload(self):
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

        nextLineIdx = 0

        # diff of index and working
        allHunks = list(parseDiff(2, 3, git_lines('diff', '--patch', '--no-color', '--no-prefix', fn)))

#        for gh in sorted(allHunks, key=lambda gh: (gh.fn, min(gh.leftstart, gh.rightstart))):
#            while max(allIndexes) < gh.leftstart:
#                r = [nextLineIdx] + [f[
#                self.rows.append(r)
#            for line in gh.difflines:
#                typech = line[0]
#                line = line[1:]
#                if typech == ' ':
#



