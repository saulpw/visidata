#!/usr/bin/env python3

import sys
import unicodedata

html_template = open('www/template.html').read()

layouts = {
'unshifted': '''Esc F1- F2- F3- F4- F5- F6- F7- F8- F9- F10- F11- F12- \u23cf-
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
CapsLock- A S D F G H J K L :- "- Enter-
Shift- Z X C V B N M <- >- ?- Shift2-
Ctrl- Alt- Cmd- Space- Cmd2- Alt2- Ctrl2-
'''
}

widths = {
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



cmds = {}
try:
    with open(sys.argv[1], 'r') as fp:
        hdrs = next(fp).strip().split('\t')
        for line in fp:
            d = dict(zip(hdrs, line.split('\t')))
            cmds[(d['shift'], d['key'])] = d
except Exception:
    raise


def get_action(shift, key, prefix=''):
    cmd = cmds.get((shift, key), None)
    if not cmd:
        return ''
    return cmd.get(prefix or 'action').replace('-', '<br/>')


def print_keyboard(layout, prefix='', shownkeys=''):
    ret = '<div id="keyboard" class="%s %s">' % (layout, prefix or 'noprefix')
    if prefix:
        ret += '<h2>for <code>%s</code> prefix</h2>' % prefix

    for rownum, row in enumerate(layouts[layout].splitlines()):
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

            if layout == 'unshifted':
                mnemonic = get_action('', key, 'mnemonic')
                action = get_action('', key, prefix)
            elif layout == 'Shift':
                mnemonic = get_action('Shift', key, 'mnemonic')
                action = get_action('Shift', key, prefix)
            elif layout == 'Ctrl':
                mnemonic = get_action('Ctrl', '^' + key, 'mnemonic')
                action = get_action('Ctrl', '^' + key, prefix)

            keyname = key[:-1] if len(key) > 2 and key[-1] == '2' else key
            style = ('style="width: %spx"' % widths[key]) if key in widths else ''

            ret += '''
            <div class="key {keyname} {fullkeyname} {class_}" {style}>
                <div class="keylabel">{keylabel}</div>
                <div class="mnemonic">{mnemonic}</div>
                <div class="action">{action}</div>
            </div>
    '''.format(keylabel=keyname,
               keyname=keyname if len(keyname) > 1 else '',
               fullkeyname=unicodedata.name(key[0]).replace(' ', '-') if len(key) == 1 else '',
               mnemonic=mnemonic,
               action=action,
               style=style,
               class_=class_)
        ret += '</div>'  # .row

    ret += '</div>'  # id=keyboard
    return ret

body = '<h1>VisiData Commands Chart</h1>'
body += '<table>'

body += '<tr><td><h2></h2></td><td>'
body += print_keyboard('unshifted', '')
body += '</td></tr>'

body += '<tr><td><h2>Shift+</h2></td><td>'
body += print_keyboard('Shift', '')
body += '</td></tr>'

body += '<td><h2>Ctrl+</h2></td><td>'
body += print_keyboard('Ctrl', '')
body += '</td></tr>'
body += '</table>'


body += '<h2>Basics and Movement</h2><table>'
body += '<td><h2></h2></td><td>'
body += print_keyboard('unshifted', '', 'hjkl/ngqe-rc')
body += '</td></tr>'

body += '<td><h2>Shift+</h2></td><td>'
body += print_keyboard('Shift', '', 'HJKL?N')
body += '</td></tr>'

body += '<td><h2>Ctrl+</h2></td><td>'
body += print_keyboard('Ctrl', '', '^ES')
body += '</td></tr>'

body += '</table>'


body += '<h2>Selections</h2><table>'
body += '<td><h2></h2></td><td>'
body += print_keyboard('unshifted', '', 'stu\\,')
body += '</td></tr>'

body += '<td><h2>Shift+</h2></td><td>'
body += print_keyboard('Shift', '', '{}|"')
body += '</td></tr>'

body += '</table>'


body += '<h2>Modifying and Clipboard</h2><table>'
body += '<td><h2></h2></td><td>'
body += print_keyboard('unshifted', '', 'adypPYe')
body += '</td></tr>'

body += '<td><h2>Shift+</h2></td><td>'
body += print_keyboard('Shift', '', 'PY^')
body += '</td></tr>'

body += '</table>'

vimkeys = 'hjklnNpP/dy'

print(html_template.format(head='<link href="keyboards_layout.css" rel="stylesheet" />',
                           title="VisiData keyboard layouts", body=body))
