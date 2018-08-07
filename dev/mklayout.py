#!/usr/bin/env python3

'Usage: $0 visidata/commands.tsv > www/layout.html'

import sys
import unicodedata

html_template = open('www/template.html').read()

cmds = {}

layouts = {
'': '''Esc F1- F2- F3- F4- F5- F6- F7- F8- F9- F10- F11- F12- \u23cf-
` 1 2 3 4 5 6 7 8 9 0 - = Backspace
Tab q w e r t y u i o p [ ] \\
CapsLock- a s d f g h j k l ; ' Enter
Shift z x c v b n m , . / Shift2
Ctrl Alt- Cmd- Space Cmd2- Alt2- Ctrl2
''',

'Shift': '''Esc- F1- F2- F3- F4- F5- F6- F7- F8- F9- F10- F11- F12- \u23cf-
~ ! @ # $ % ^ & * ( ) _ + Backspace-
Tab- Q W E R T Y U I O P { } |
CapsLock- A S D F G H J K L : ＂ Enter-
Shift- Z X C V B N M < > ? Shift2-
Ctrl- Alt- Cmd- Space- Cmd2- Alt2- Ctrl2-
''',
'Ctrl': '''Esc- F1- F2- F3- F4- F5- F6- F7- F8- F9- F10- F11- F12- \u23cf-
~- !- @ #- $- %- ^ &- *- (- )- _ +- Backspace-
Tab- Q W E R T Y U I O P [ ] \\
CapsLock- A S D F G H J- K L :- "- Enter-
Shift- Z X C V B N M- <- >- ?- Shift2-
Ctrl- Alt- Cmd- Space- Cmd2- Alt2- Ctrl2-
'''
}

pixel_widths = {
    '\u23cf': 63,
    'Backspace': 102,
    'Tab': 72,
    '\\': 82,
    '|': 82,
    'CapsLock': 88,
    'Enter': 123,
    'Shift': 126,
    'Shift2': 142,
    'Ctrl:': 82,
    'Cmd': 82,
    'Alt': 66,
    'Space': 368,
    'Cmd2': 86,
    'Alt2': 70,
    'Ctrl2': 89,
}

#widths = {k: '%.02f%%' % (v/9.50) for k, v in pixel_widths.items()}
widths = {k: '%spx' % v for k, v in pixel_widths.items()}

def load_tsv(fn):
    with open(fn, 'r') as fp:
        hdrs = next(fp).strip().split('\t')
        for line in fp:
            yield dict(zip(hdrs, line.split('\t')))

def get_command(sheetnames, shift, key, prefix):
    for sheet in sheetnames:
        cmd = cmds.get((sheet, prefix, shift, key), None)
        if cmd:
            return cmd


def print_keyboard(sheetnames, shift, prefix='', shownkeys=''):
    ret = '<div class="%s %s">' % (prefix, shift)

    for rownum, row in enumerate(layouts[shift].splitlines()):
        if rownum == 0:  # function row
            ret += '<div class="row mac-fkeys">'
        else:
            ret += '<div class="row">'

        for key in row.split():
            class_ = ''

            if shownkeys and key not in shownkeys:
                class_ = ' na'

            if len(key) > 1 and key[-1] == '-':  # key is not available in this layout
                key = key[:-1]
                class_ = ' na'

            if shift == '':
                cmd = get_command(sheetnames, '', key, prefix)
            elif shift == 'Shift':
                cmd = get_command(sheetnames, 'Shift', key, prefix)
            elif shift == 'Ctrl':
                cmd = get_command(sheetnames, 'Ctrl', '^' + key, prefix)
            else:
                cmd = None

            action = cmd['longname'] if cmd else ''

            if action.count('-') > 1 or max((len(p) for p in action.split('-'))) > 8:
                action = action.replace('-', ' ')
                class_ += ' tri'
            else:
                action = action.replace('-', '<br/>')

            keyname = key[:-1] if len(key) > 2 and key[-1] == '2' else key
            style = ('style="width: %s"' % widths[key]) if key in widths else ''

            if keyname == shift:
                class_ += ' depressed'

            if shift == 'Ctrl' and 'na' not in class_:
                keyname = '^' + keyname

            ret += '''
            <div class="key {keyname} {fullkeyname} {class_}" {style}>
                <div class="keylabel">{keylabel}</div>
                <div class="action"><a title="{helpstr}">{action}</a></div>
            </div>
    '''.format(keylabel=keyname,
               keyname=keyname if len(keyname) > 1 else '',
               fullkeyname=unicodedata.name(key[0]).replace(' ', '-') if len(key) == 1 else '',
               action=action,
               style=style,
               helpstr=cmd['helpstr'].strip() if cmd else '',
               class_=class_)
        ret += '</div>'  # .row

    ret += '</div>'  # id=keyboard
    return ret

def keyboard_layout(sheetnames, prefix, shift, shown=''):
    sheetname = sheetnames[0]
    ret = '<div class="layout" id="%s-%s-%s">' % (sheetname, prefix or "noprefix", shift or 'unshifted')
    ret += print_keyboard(sheetnames, shift.capitalize(), prefix, shown)  # capitalize shift
    ret += '</div>'
    return ret


def keyboard_layouts(sheetnames, prefix, shown=''):
    ret = keyboard_layout(sheetnames, prefix, '', shown)
    ret += keyboard_layout(sheetnames, prefix, 'shift', shown)
    ret += keyboard_layout(sheetnames, prefix, 'ctrl', shown)
    return ret


def get_shift(k):
    if len(k) == 2 and k[0] == '^':
        return 'Ctrl'
    elif len(k) == 1 and k.isupper():
        return 'Shift'
    else:
        return ''


def main():
    for cmd in load_tsv(sys.argv[1]):
        cmds[(cmd['sheet'], cmd['prefix'], get_shift(cmd['key']), cmd['key'])] = cmd

    body = '<h1>VisiData Commands Chart</h1>'

    body += '''
    <div id="keyboard-outer">
    <div>
    <h2>Keystrokes for
    <select id="sheet" name="sheet" onchange="set_layout(get_layout())">
        <option value="Sheet">Sheet</option>
        <option value="Canvas">Canvas</option>
    </select>:
    <code><select id="prefix" name="prefix" onchange="set_layout(get_layout())">
        <option value="noprefix" selected>(no prefix)</option>
        <option value="g">g</option>
        <option value="z">z</option>
        <option value="gz">gz</option>
    </select></code>
    <code><select id="shift" name="shift" onchange="set_layout(get_layout())">
        <option value="unshifted" selected>(unshifted)</option>
        <option value="shift">Shift</option>
        <option value="ctrl">Ctrl</option>
    </select></code></h2>
    </div>
    <div id="keyboard">
    '''

    # sheets = set(cmd['sheet'] for cmd in cmds.values())
    sheets = { 'Sheet': 'Sheet global'.split(),
               'Canvas': 'Canvas Plotter'.split() }

    for sheetnames in sheets.values():
        body += keyboard_layouts(sheetnames, '')
        body += keyboard_layouts(sheetnames, 'g')
        body += keyboard_layouts(sheetnames, 'z')
        body += keyboard_layouts(sheetnames, 'gz')

    body += '</div>' # keyboard
    body += '</div>' # keyboard-outer

# 'Basics and Movement': list('hjkl/ngqe-rcHJKL?NS') + ['^E'],
# 'Selections': 'stu\\,{}|"
# 'Modifying and Clipboard': 'adypPYe^'
# 'vimkeys': 'hjklnNpP/dy'

    js = '''<script>

function get_layout() {
    layouts = document.getElementsByClassName('layout');
    for (var i=0; i < layouts.length; ++i) {
        e = layouts[i];
        e.classList.remove('shown');
    }

    e = document.getElementById('prefix')
    prefix = e.options[e.selectedIndex].value

    e = document.getElementById('shift')
    shift = e.options[e.selectedIndex].value

    e = document.getElementById('sheet')
    sheet = e.options[e.selectedIndex].value

    return sheet+'-'+prefix+'-'+shift
}

function set_layout(layoutid) {
    e = document.getElementById(layoutid);
    if (e) {
        e.classList.add('shown');
    } else {
        alert("no layout " + layoutid)
    }
}

window.onload = function () { set_layout('Sheet-noprefix-unshifted') }
</script>
    '''
    print(html_template.format(head='<link href="kblayout.css" rel="stylesheet" />'+js,
                               title="VisiData keyboard layouts", body=body))


main()
