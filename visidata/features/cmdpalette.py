import collections
from visidata import BaseSheet, vd, CompleteKey, clipdraw, HelpSheet, colors, AcceptInput, AttrDict


vd.theme_option('color_cmdpalette', 'black on 72', 'base color of command palette')
vd.theme_option('disp_cmdpal_max', 5, 'max number of suggestions for command palette')



def _format_match(s, positions):
    out = list(s)
    for p in positions:
        out[p] = f'[:red]{out[p]}[/]'
    return "".join(out)

def make_acceptor(value):
    def _exec(v, i):
        raise AcceptInput(value)
    return _exec


@BaseSheet.api
def inputPalette(sheet, prompt, items, value_key='', formatter=lambda m, item, trigger_key: f'{trigger_key} {item}', **kwargs):
    bindings = dict()

    def _draw_palette(value):
        words = value.lower().split()

        matches = vd.fuzzymatch(items, words)

        # do the drawing
        h, w = sheet._scr.getmaxyx()
        cmdpal_h = min(h-2, sheet.options.disp_cmdpal_max)
        m_max = min(len(matches), cmdpal_h)

        for i, m in enumerate(matches[:m_max]):
            trigger_key = ' '

            if i < 9:
                trigger_key = f'{i+1}'
                bindings[trigger_key] = make_acceptor(m.match[value_key])

            match_summary = formatter(m, m.match, trigger_key)

            clipdraw(sheet._scr, h-(m_max+1)+i, 0, match_summary, colors.color_cmdpalette, w=120)

        # add some empty rows for visual appeal and dropping previous (not-anymore-)matches
        for i in range(cmdpal_h - m_max):
            clipdraw(sheet._scr, h-(cmdpal_h+1)+i, 0, ' ', colors.color_cmdpalette, w=120)

        return None

    completer = CompleteKey(sorted(item[value_key] for item in items))
    return vd.input(prompt,
            completer=completer,
            updater=_draw_palette,
            bindings=bindings,
            **kwargs)

@BaseSheet.api
def inputLongname(sheet):
    prompt = 'command name: '
    # get set of commands possible in the sheet
#    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    this_sheets_help = HelpSheet('', source=sheet)
    this_sheets_help.ensureLoaded()
    vd.sync()
    this_sheet_commands = [
        AttrDict(longname=row.longname,
                 description=this_sheets_help.cmddict[(row.sheet, row.longname)].helpstr)
        for row in this_sheets_help.rows
    ]
    assert this_sheet_commands

    def _fmt_cmdpal_summary(match, row, trigger_key):
        keystrokes = this_sheets_help.revbinds.get(row.longname, [None])[0] or ' '
        formatted_longname = _format_match(row.longname, match.positions.get('longname', []))
        vd.status(str(match.positions), formatted_longname)
        formatted_name = f'[:onclick {row.longname}]{formatted_longname}[/]'
        r = f' [:keystrokes]{keystrokes.rjust(len(prompt)-5)}[/]  '
        r += f'[:keystrokes]{trigger_key}[/] {formatted_name}'
        if row.description:
            formatted_desc = _format_match(row.description, match.positions.get('description', []))
            r += f' - {formatted_desc}'
        if vd.options.debug:
            debug_info = f'[{m.score}]'
            r = debug_info + r[len(debug_info):]
        return r

    return sheet.inputPalette(prompt, this_sheet_commands,
                              value_key='longname',
                              formatter=_fmt_cmdpal_summary,
                              type='longname')


@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.fail(f'no command {longname}')
    sheet.execCommand(longname)


vd.addCommand('Space', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
