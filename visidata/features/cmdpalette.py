import collections
from functools import partial
from visidata import DrawablePane, BaseSheet, vd, VisiData, CompleteKey, clipdraw, HelpSheet, colors, AcceptInput, AttrDict, drawcache_property


vd.theme_option('color_cmdpalette', 'black on 72', 'base color of command palette')
vd.theme_option('disp_cmdpal_max', 10, 'max number of suggestions for command palette')

vd.help_longname = '''# Choose Command
Start typing a command longname or keyword in its helpstring.

- `Enter` to execute top command.
- `Tab` to highlight top command.

## When Command Highlighted

- `Tab`/`Shift+Tab` to cycle highlighted command.
- `Enter` to execute highlighted command.
- `0-9` to execute numbered command.
'''

def add_to_input(v, i, value=''):
    items = list(v.split())
    if not v or v.endswith(' '):
        items.append(value)
    else:
        items[-1] = value
    v = ' '.join(items) + ' '
    return v, len(v)


def accept_input(v, i, value=None):
    raise AcceptInput(v if value is None else value)

def accept_input_if_subset(v, i, value=''):
    # if no input, accept value under cmd palette cursor
    if not v:
        raise AcceptInput(value)

    # if the last item is a partial match, replace it with the full value
    parts = v.split()
    if value and value.startswith(parts[-1]):
        v = ' '.join(parts[:-1] + [value])

    raise AcceptInput(v)

@VisiData.lazy_property
def usedInputs(vd):
    return collections.defaultdict(int)

@DrawablePane.after
def execCommand2(sheet, cmd, *args, **kwargs):
    vd.usedInputs[cmd.longname] += 1

@BaseSheet.api
def inputPalette(sheet, prompt, items,
                 value_key='key',
                 formatter=lambda m, item, trigger_key: f'{trigger_key} {item}',
                 multiple=False,
                 **kwargs):
    if sheet.options.disp_expert >= 5:
        return vd.input(prompt,
                completer=CompleteKey(sorted(item[value_key] for item in items)),
                **kwargs)

    bindings = dict()

    tabitem = -1

    def tab(n, nitems):
        nonlocal tabitem
        if not nitems: return None
        tabitem = (tabitem + n) % nitems

    def _draw_palette(value):
        words = value.lower().split()

        if multiple and words:
            if value.endswith(' '):
                finished_words = words
                unfinished_words = []
            else:
                finished_words = words[:-1]
                unfinished_words = [words[-1]]
        else:
            unfinished_words = words
            finished_words = []

        unuseditems = [item for item in items if item[value_key] not in finished_words]

        matches = vd.fuzzymatch(unuseditems, unfinished_words)

        h = sheet.windowHeight
        w = min(100, sheet.windowWidth)
        nitems = min(h-1, sheet.options.disp_cmdpal_max)

        useditems = []
        palrows = []

        for m in matches[:nitems]:
            useditems.append(m.match)
            palrows.append((m, m.match))

        favitems = sorted([item for item in unuseditems if item not in useditems],
                          key=lambda item: -vd.usedInputs.get(item[value_key], 0))

        for item in favitems[:nitems-len(palrows)]:
            palrows.append((None, item))

        navailitems = min(len(palrows), nitems)

        bindings['Ctrl+I'] = lambda *args: tab(1, navailitems) or args
        bindings['Shift+Tab'] = lambda *args: tab(-1, navailitems) or args

        for i in range(nitems-len(palrows)):
            palrows.append((None, None))

        used_triggers = set()
        for i, (m, item) in enumerate(palrows):
            trigger_key = ''
            if tabitem >= 0 and item:
                tkey = f'{i+1}'[-1]
                if tkey not in used_triggers:
                    trigger_key = tkey
                    bindings[trigger_key] = partial(add_to_input if multiple else accept_input, value=item[value_key])
                    used_triggers.add(trigger_key)

            attr = colors.color_cmdpalette

            if tabitem < 0 and palrows:
                _ , topitem = palrows[0]
                if not topitem: return
                if multiple:
                    bindings[' '] = partial(add_to_input, value=topitem[value_key])
                    bindings['Enter'] = partial(accept_input_if_subset, value=topitem[value_key])
                else:
                    bindings['Enter'] = partial(accept_input, value=topitem[value_key])
            elif item and i == tabitem:
                if not item: return
                if multiple:
                    bindings['Enter'] = partial(accept_input_if_subset, value=item[value_key])
                    bindings[' '] = partial(add_to_input, value=item[value_key])
                else:
                    bindings['Enter'] = partial(accept_input, value=item[value_key])
                attr = colors.color_menu_spec

            match_summary = formatter(m, item, trigger_key) if item else ' '

            clipdraw(sheet._scr, h-nitems-1+i, 0, match_summary, attr, w=w)

        return None

    completer = CompleteKey(sorted(item[value_key] for item in items))
    return vd.input(prompt,
            completer=completer,
            updater=_draw_palette,
            bindings=bindings,
            **kwargs)


def cmdlist(sheet):
    return [
            AttrDict(longname=row.longname,
                     description=sheet.cmddict[(row.sheet, row.longname)].helpstr)
        for row in sheet.rows
    ]
HelpSheet.cmdlist = drawcache_property(cmdlist)


@BaseSheet.api
def inputLongname(sheet):
    prompt = 'command name: '
    # get set of commands possible in the sheet
    this_sheets_help = HelpSheet('', source=sheet)
    vd.sync(this_sheets_help.ensureLoaded())

    def _fmt_cmdpal_summary(match, row, trigger_key):
        keystrokes = this_sheets_help.revbinds.get(row.longname, [None])[0] or ' '
        formatted_longname = match.formatted.get('longname', row.longname) if match else row.longname
        formatted_name = f'[:bold][:onclick {row.longname}]{formatted_longname}[/][/]'
        if vd.options.debug and match:
            keystrokes = f'[{match.score}]'
        r = f' [:keystrokes]{keystrokes.rjust(len(prompt)-5)}[/]  '
        if trigger_key:
            r += f'[:keystrokes]{trigger_key}[/]'
        else:
            r += ' '

        r += f' {formatted_name}'
        if row.description:
            formatted_desc = match.formatted.get('description', row.description) if match else row.description
            r += f' - {formatted_desc}'
        return r

    return sheet.inputPalette(prompt, this_sheets_help.cmdlist,
                              value_key='longname',
                              formatter=_fmt_cmdpal_summary,
                              help=vd.help_longname,
                              type='longname')

@BaseSheet.api
def inputLongnameSimple(sheet):
    'Input a command longname without using the command palette.'
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)), type='longname')


@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.fail(f'no command {longname}')
    sheet.execCommand(longname)


vd.addCommand('Space', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
vd.addCommand('zSpace', 'exec-longname-simple', 'exec_longname(inputLongnameSimple())', 'execute command by its longname')
