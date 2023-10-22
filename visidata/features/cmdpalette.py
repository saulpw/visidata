import collections
from visidata import BaseSheet, vd, CompleteKey, clipdraw, HelpSheet, colors, AcceptInput


vd.option('color_cmdpalette', 'black on 72', 'base color of command palette')
vd.option('disp_cmdpal_max', 5, 'max number of suggestions for command palette')


def _format_match(s, positions):
    out = list(s)
    for p in positions:
        out[p] = f'[:bold]{out[p]}[/]'
    return "".join(out)


@BaseSheet.api
def inputLongname(sheet):
    max_matches = vd.options.disp_cmdpal_max
    label = 'command name: '
    # get set of commands possible in the sheet
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    this_sheets_help = HelpSheet('', source=sheet)
    this_sheets_help.ensureLoaded()
    Match = collections.namedtuple('Match', 'name formatted_name keystrokes description score')
    bindings = dict()

    def longname_executor(name):
        def _exec(v, i):
            raise AcceptInput(name)
        return _exec

    def cmdpal_matcher(value):
        # collect data
        matches = []
        words = value.lower().split()
        for row in this_sheets_help.rows:
            description = this_sheets_help.cmddict[(row.sheet, row.longname)].helpstr
            longname_score, desc_score = 0, 0
            positions_name = set()
            positions_desc = set()
            for word in words:
                result_name = vd.fuzzymatch(row.longname, word)
                result_desc = vd.fuzzymatch(description.lower(), word)
                # if a word matches neither, we can skip the row
                if result_name.start == -1 and result_desc.start == -1:
                    score = 0
                    break
                longname_score = longname_score+result_name.score
                desc_score = desc_score+result_desc.score
                if result_name.positions:
                    positions_name.update(result_name.positions)
                if result_desc.positions:
                    positions_desc.update(result_desc.positions)
            # prefer if match is either fully on longname or on description
            score = longname_score**2 + desc_score**2
            if score > 0:
                keystrokes = this_sheets_help.revbinds.get(row.longname, [None])[0]
                formatted_name = f'[:onclick {row.longname}]{_format_match(row.longname, positions_name)}[/]'
                formatted_desc = _format_match(description, positions_desc)
                matches.append(Match(row.longname, formatted_name, keystrokes, formatted_desc, score))
        matches.sort(key=lambda m: -m.score)

        # do the drawing
        h, w = sheet._scr.getmaxyx()
        n = min(len(matches), max_matches)
        for i in range(n):
            m = matches[i]
            if i < 9:
                trigger_key = f'{i+1}'
                bindings[trigger_key] = longname_executor(m.name)
            else:
                trigger_key = ' '
            buffer = ' '*(len(label)-2)
            # TODO: put keystrokes into buffer
            match_summary = f'{buffer}[:keystrokes]{trigger_key}[/] {m.formatted_name}'
            if m.keystrokes:
                match_summary += f' ([:keystrokes]{m.keystrokes}[/])'
            if m.description:
                match_summary += f' - {m.description}'
            if vd.options.debug:
                debug_info = f'[{m.score}]'
                match_summary = debug_info + match_summary[len(debug_info):]
            clipdraw(sheet._scr, h-(n+1)+i, 0, match_summary, colors.color_cmdpalette, w=120)
        # add some empty rows for visual appeal and dropping previous (not-anymore-)matches
        for i in range(max_matches-n):
            try:
                clipdraw(sheet._scr, h-(max_matches+1)+i, 0, ' ', colors.color_cmdpalette, w=120)
            except Exception as e:
                breakpoint()
        # TODO: bug: terminal not high enough => will break.

        return None
    return vd.input(label, completer=CompleteKey(sorted(longnames)), type='longname', updater=cmdpal_matcher,
                    bindings=bindings)

@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.fail(f'no command {longname}')
    sheet.execCommand(longname)


vd.addCommand('Space', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
