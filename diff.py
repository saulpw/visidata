from vdtui import *
from git import GitSheet

def openDiff(fn, ref1, ref2):
    diff = git_lines('diff', '-U999999', ref1, ref2, fn)
    vs = DiffViewer(fn, list(diff))
    vd().push(vs)
    return vs

# rowdef: [typech, line1, line2]
class DiffViewer(GitSheet):
    def __init__(self, name, patchlines):
        super().__init__(name, patchlines)
        self.columns = [
            ColumnItem('1', 1, width=vd().windowWidth//2-1),
            ColumnItem('2', 2, width=vd().windowWidth//2-1),
        ]
        self.addColorizer(Colorizer('row', 4, DiffViewer.colorDiffRow))

    def reload(self):
        patchlines = self.source
        self.rows = []
        nextDelIdx = None
        for line in patchlines[3:]:  # diff without the patch headers
            typech = line[0]
            line = line[1:]
            if typech == '-':
                self.rows.append([typech, line, None])
                if nextDelIdx is None:
                    nextDelIdx = len(self.rows)-1
            elif typech == '+':
                if nextDelIdx is not None:
                    if nextDelIdx < len(self.rows):
                        self.rows[nextDelIdx][2] = line
                        nextDelIdx += 1
                        continue

                self.rows.append([typech, None, line])
                nextDelIdx = None
            elif typech == ' ':
                self.rows.append([typech, line, line])
                nextDelIdx = None
            else:
                continue  # header

    def colorDiffRow(self, c, row, v):
        if row[1] != row[2]:
            if row[1] is None:
                return 'green'  # addition
            elif row[2] is None:
                return 'red'  # deletion
            else:
                return 'yellow'  # difference


addGlobals(globals())
