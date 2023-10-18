import collections
from visidata import BaseSheet, vd, CompleteKey, clipdraw, HelpSheet, colors

vd.option('color_cmdpalette', 'black on 72', 'base color of command palette')
def levenshtein(a, b):
    # source: https://en.wikipedia.org/wiki/Levenshtein_distance#Iterative_with_full_matrix
    d = []
    m, n = len(a), len(b)
    for _ in range(m+1):
        row = []
        for _ in range(n+1):
            row.append(0)
        d.append(row)
    for i in range(1, m+1):
        d[i][0] = i
    for j in range(1, n+1):
        d[0][j] = j
    for j in range(n):
        for i in range(m):
            if a[i] == b[j]:
                cost = 0
            else:
                cost = 1
            d[i+1][j+1] = min(d[i][j+1]+1, d[i+1][j]+1, d[i][j]+cost)
    return d[m][n]


@BaseSheet.api
def inputLongname(sheet):
    # get set of commands possible in the sheet
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    this_sheets_help = HelpSheet("", source=sheet)
    this_sheets_help.ensureLoaded()
    Match = collections.namedtuple('Match', 'name keystrokes description distance')
    def myupdater(value):
        # collect data
        matches = []
        letters = set(value)
        for row in this_sheets_help.rows:
            distance = levenshtein(value, row.longname)
            if letters.issubset(set(row.longname)):
                description = this_sheets_help.cmddict[(row.sheet, row.longname)].helpstr
                keystrokes = this_sheets_help.revbinds.get(row.longname, [None])[0]
                matches.append(Match(row.longname, keystrokes, description, distance))
        matches.sort(key=lambda m: m[3])

        # do the drawing
        h, w = sheet._scr.getmaxyx()
        n = min(len(matches), 5)
        for i in range(n):
            m = matches[i]
            clipdraw(sheet._scr, h-(n+1)+i, 0, f"[{m.distance}] [:onclick {m.name}]{m.name}[:] ({m.keystrokes}) - {m.description}", colors.color_cmdpalette, w=w)
        # add some empty rows for visual appeal and dropping previous (not-anymore-)matches
        for i in range(5-n):
            clipdraw(sheet._scr, h-6+i, 0, " ", 0, w=w)

        return None
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)), type='longname', updater=myupdater,
                    bindings={"1": lambda v, i: vd.sheet.exec_longname("melt")})

@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.warning(f'no command {longname}')
        return
    sheet.execCommand(longname)

vd.addCommand(' ', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
