import string
import visidata


visidata.vd.prettykeys_trdict = {
        ' ': 'Space',  # must be first
        '^[': 'Alt+',
        '^J': 'Enter',
        '^M': 'Enter',
        '^I': 'Tab',
        'KEY_BTAB': 'Shift+Tab',
        '^@': 'Ctrl+Space',
        'KEY_UP':    'Up',
        'KEY_DOWN':  'Down',
        'KEY_LEFT':  'Left',
        'KEY_RIGHT': 'Right',
        'KEY_HOME':  'Home',
        'KEY_END':   'End',
        'KEY_EOL':   'End',
        'KEY_PPAGE': 'PgUp',
        'KEY_NPAGE': 'PgDn',

        'kUP':       'Shift+Up',
        'kDN':       'Shift+Down',
        'kUP5':      'Ctrl+Up',
        'kDN5':      'Ctrl+Down',
        'kLFT5':     'Ctrl+Left',
        'kRIT5':     'Ctrl+Right',
        'kHOM5':     'Ctrl+Home',
        'kEND5':     'Ctrl+End',
        'kPRV5':     'Ctrl+PgUp',
        'kNXT5':     'Ctrl+PgDn',
        'KEY_IC5':   'Ctrl+Ins',
        'KEY_DC5':   'Ctrl+Del',
        'kDC5':      'Ctrl+Del',
        'KEY_SDC':   'Shift+Del',

        'KEY_IC':    'Ins',
        'KEY_DC':    'Del',

        'KEY_SRIGHT':'Shift+Right',
        'KEY_SR':    'Shift+Up',
        'KEY_SF':    'Shift+Down',
        'KEY_SLEFT': 'Shift+Left',
        'KEY_SHOME': 'Shift+Home',
        'KEY_SEND':  'Shift+End',
        'KEY_SPREVIOUS': 'Shift+PgUp',
        'KEY_SNEXT': 'Shift+PgDn',

        'KEY_BACKSPACE': 'Bksp',
        'BUTTON1_RELEASED': 'LeftBtnUp',
        'BUTTON2_RELEASED': 'MiddleBtnUp',
        'BUTTON3_RELEASED': 'RightBtnUp',
        'BUTTON1_PRESSED': 'LeftClick',
        'BUTTON2_PRESSED': 'MiddleClick',
        'BUTTON3_PRESSED': 'RightClick',
        'BUTTON4_PRESSED': 'ScrollUp',
        'BUTTON5_PRESSED': 'ScrollDown',
        'REPORT_MOUSE_POSITION': 'ScrollDown',
        '2097152': 'ScrollDown',
    }

for i in range(1, 13):
    d = visidata.vd.prettykeys_trdict
    d[f'KEY_F({i})'] = f'F{i}'
    d[f'KEY_F({i+12})'] = f'Shift+F{i}'
    d[f'KEY_F({i+24})'] = f'Ctrl+F{i}'
    d[f'KEY_F({i+36})'] = f'Ctrl+Shift+F{i}'
    d[f'KEY_F({i+48})'] = f'Alt+F{i}'
    d[f'KEY_F({i+60})'] = f'Alt+Shift+F{i}'


@visidata.VisiData.api
def prettykeys(vd, key):
    if not key:
        return key

    for k, v in vd.prettykeys_trdict.items():
        key = key.replace(k, v)

    # replace ^ with Ctrl but not if ^ is last char
    key = key[:-1].replace('^', 'Ctrl+')+key[-1]
    # 1497: allow Shift+ for Alt keys
    if key[-1] in string.ascii_uppercase and ('+' not in key or 'Alt+' in key) and '_' not in key:
        key = key[:-1] + 'Shift+' + key[-1]

    return key.strip()
