from visidata import vd, Column, VisiData, ItemColumn, Path, AttrDict, date

from .gitsheet import GitSheet


@VisiData.api
def git_blame(vd, gitpath, args, **kwargs):
    if args and not args[-1].startswith('-'):
        fn = args[-1]
        return GitBlame('blame', fn, source=Path(fn), **kwargs)


class FormatColumn(Column):
    def calcValue(self, row):
        return self.expr.format(**row)


# rowdef: (hdr, orig_linenum, linenum, line)
#   hdr = { 'sha': .., 'orig_linenum': .., 'final_linenum': .. }
# source = GitSheet; .gitfile=GitFile
class GitBlame(GitSheet):
    rowtype = 'lines'
    guide = '''
        # git blame
    '''
    columns = [
        ItemColumn('sha', width=0),
        ItemColumn('orig_linenum', width=0, type=int),
        ItemColumn('final_linenum', width=0, type=int),
        ItemColumn('author', width=15),
        ItemColumn('author_time', width=13, type=date),
        FormatColumn('committer', width=0, expr='{committer} {committer_mail}'),
        ItemColumn('committer_time', width=0, type=date),
        ItemColumn('linenum', width=6, type=int),
        ItemColumn('line', width=72),
    ]

    def iterload(self):
        lines = list(self.git_lines('blame', '--porcelain', str(self.source)))
        i = 0
        headers = {}  # [sha1] -> hdr
        while i < len(lines):
            # header
            parts = lines[i].split()
            sha, orig, final = parts[:3]
            if len(parts) > 3:
                nlines_this_group = parts[3]

            if sha not in headers:
                hdr = AttrDict(sha=sha, orig_linenum=orig, final_linenum=final)
                headers[sha] = hdr
            else:
                hdr = headers[sha]

            while lines[i][0] != '\t':
                try:
                    k, v = lines[i].split(maxsplit=1)
                    k = k.replace('-', '_')
                    if '_time' in k:
                        v = int(v)
                    hdr[k] = v
                except Exception:
                    vd.status(lines[i])
                i += 1

            yield AttrDict(
                linenum=final,
                line=lines[i][1:],
                **hdr
            )
            i += 1


#GitBlame.addCommand(ENTER, 'diff-line', 'openDiff(str(gitfile), cursorRow[0]["sha"]+"^", cursorRow[0]["sha"])', 'open diff of the commit when this line changed')

#GitStatus.addCommand(None, 'git-blame', 'vd.push(GitBlame(cursorRow, source=sheet))', 'push blame for this file')
