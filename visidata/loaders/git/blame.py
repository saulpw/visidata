from vdtui import *
from git import GitSheet

# row is (hdr, orig_linenum, linenum, line)
#   hdr = { 'sha': .., 'orig_linenum': .., 'final_linenum': .. }
class GitBlame(GitSheet):
    commands = GitSheet.commands + [
        Command(ENTER, 'openDiff(str(source), cursorRow[0]["sha"]+"^", cursorRow[0]["sha"])', 'open diff of the commit when this line changed'),
    ]

    columns = [
        Column('sha', width=8, getter=lambda r: r[0]['sha']),
        Column('orig_linenum', width=0, getter=lambda r: r[0]['orig_linenum']),
        Column('orig_linenum1', width=0, getter=lambda r: r[1]),
        Column('final_linenum', width=0, getter=lambda r: r[0]['final_linenum']),
        Column('author', width=10, getter=lambda r: '{author}'.format(**r[0])),
        Column('author_date', width=13, type=date, getter=lambda r: int(r[0].get('author-time', 0))),
        Column('committer', width=0, getter=lambda r: '{committer} {committer-mail}'.format(**r[0])),
        Column('committer_date', width=0, type=date, getter=lambda r: int(r[0].get('committer-time', 0)) or None),
        Column('linenum', width=5, getter=lambda r: r[2]),
        Column('code', getter=lambda r: r[3]),
    ]

    def __init__(self, gf, ref='HEAD'):
        super().__init__('blame_'+str(gf), gf)

    def reload(self):
        self.rows = []

        lines = list(git_lines('blame', '--porcelain', str(self.source)))
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
                except:
                    status(lines[i])
                i += 1

            self.rows.append((hdr, orig, final, lines[i][1:]))
            i += 1

addGlobals(globals())
