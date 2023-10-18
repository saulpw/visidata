import collections
from visidata import BaseSheet, vd, CompleteKey, clipdraw, HelpSheet, colors, EscapeException

vd.option('color_cmdpalette', 'black on 72', 'base color of command palette')
vd.option('cmdpal_max_matches', 5, 'max number of suggestions for command palette')
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
    max_matches = vd.options.cmdpal_max_matches
    label = "command name: "
    # get set of commands possible in the sheet
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    this_sheets_help = HelpSheet("", source=sheet)
    this_sheets_help.ensureLoaded()
    Match = collections.namedtuple('Match', 'name keystrokes description distance')
    bindings = dict()

    def longname_executor(name):
        def _exec(v, i):
            vd.sheet.exec_longname(name)
            raise EscapeException('^[')
        return _exec

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
        n = min(len(matches), max_matches)
        for i in range(n):
            m = matches[i]
            if i < 9:
                trigger_key = f"{i+1}"
                bindings[trigger_key] = longname_executor(m.name)
            else:
                trigger_key = " "
            buffer = " "*(len(label)-2)
            match_summary = f"{buffer}{trigger_key} [:onclick {m.name}]{m.name}[:] ({m.keystrokes}) - {m.description}"
            if vd.options.debug:
                debug_info = f"[{m.distance}]"
                match_summary = debug_info + match_summary[len(debug_info):]
            clipdraw(sheet._scr, h-(n+1)+i, 0, match_summary, colors.color_cmdpalette, w=w)
        # add some empty rows for visual appeal and dropping previous (not-anymore-)matches
        for i in range(max_matches-n):
            clipdraw(sheet._scr, h-(max_matches+1)+i, 0, " ", colors.color_cmdpalette, w=w)

        return None
    return vd.input(label, completer=CompleteKey(sorted(longnames)), type='longname', updater=myupdater,
                    bindings=bindings)

@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.warning(f'no command {longname}')
        return
    sheet.execCommand(longname)

vd.addCommand(' ', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
