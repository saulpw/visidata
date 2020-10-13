from visidata import *
from .git import GitSheet
from .status import GitStatus


# rowdef: (hdr, orig_linenum, linenum, line)
#   hdr = { 'sha': .., 'orig_linenum': .., 'final_linenum': .. }
# source = GitSheet; .gitfile=GitFile
class GitBlame(GitSheet):
    rowtype = 'lines'
    columns = [
        Column('sha', width=8, getter=lambda c,r: r[0]['sha']),
        Column('orig_linenum', width=0, getter=lambda c,r: r[0]['orig_linenum']),
        Column('orig_linenum1', width=0, getter=lambda c,r: r[1]),
        Column('final_linenum', width=0, getter=lambda c,r: r[0]['final_linenum']),
        Column('author', width=10, getter=lambda c,r: '{author}'.format(**r[0])),
        Column('author_date', width=13, type=date, getter=lambda c,r: int(r[0].get('author-time', 0))),
        Column('committer', width=0, getter=lambda c,r: '{committer} {committer-mail}'.format(**r[0])),
        Column('committer_date', width=0, type=date, getter=lambda c,r: int(r[0].get('committer-time', 0)) or None),
        Column('linenum', width=5, getter=lambda c,r: r[2]),
        Column('HEAD', getter=lambda c,r: r[3]),
        Column('index', getter=lambda c,r: r[3]),
        Column('working', getter=lambda c,r: r[3]),
    ]

    def __init__(self, gitfile, source=None, ref='HEAD'):
        super().__init__(str(gitfile), gitfile=gitfile, source=source, ref=ref)

    def reload(self):
        self.rows = []

        lines = list(self.git_lines('blame', '--porcelain', str(self.gitfile)))
        i = 0
        headers = {}  # [sha1] -> hdr
        while i < len(lines):
            # header
            parts = lines[i].split()
            sha, orig, final = parts[:3]
            if len(parts) > 3:
                nlines_this_group = parts[3]

            if sha not in headers:
                hdr = {
                    'sha': sha,
                    'orig_linenum': orig,
                    'final_linenum': final,
                }
                headers[sha] = hdr
            else:
                hdr = headers[sha]

            while lines[i][0] != '\t':
                try:
                    k, v = lines[i].split(maxsplit=1)
                    hdr[k] = v
                except Exception:
                    status(lines[i])
                i += 1

            self.addRow((hdr, orig, final, lines[i][1:]))
            i += 1

GitBlame.addCommand(ENTER, 'diff-line', 'openDiff(str(gitfile), cursorRow[0]["sha"]+"^", cursorRow[0]["sha"])', 'open diff of the commit when this line changed')

GitStatus.addCommand(None, 'git-blame', 'vd.push(GitBlame(cursorRow, source=sheet))', 'push blame for this file'),


GitFileSheet = GitBlame
