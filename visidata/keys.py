import string
import visidata


visidata.vd.prettykeys_trdict = {
        ' ': 'Space',  # must be first
        '^[': 'Alt+',
        '^J': 'Enter',
        '^M': 'Enter',
        '^I': 'Tab',
        'KEY_UP':    'Up',
        'KEY_DOWN':  'Down',
        'KEY_LEFT':  'Left',
        'KEY_RIGHT': 'Right',
        'KEY_HOME':  'Home',
        'KEY_END':   'End',
        'KEY_EOL':   'End',
        'KEY_PPAGE': 'PgUp',
        'KEY_NPAGE': 'PgDn',

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
        'BUTTON1_PRESSED': 'LeftClick',
        'BUTTON2_PRESSED': 'MiddleClick',
        'BUTTON3_PRESSED': 'RightClick',
        'BUTTON4_PRESSED': 'ScrollwheelUp',
        'REPORT_MOUSE_POSITION': 'ScrollwheelDown',
        'KEY_F(1)': 'F1',
        'KEY_F(2)': 'F2',
        'KEY_F(3)': 'F3',
        'KEY_F(4)': 'F4',
        'KEY_F(5)': 'F5',
        'KEY_F(6)': 'F6',
        'KEY_F(7)': 'F7',
        'KEY_F(8)': 'F8',
        'KEY_F(9)': 'F9',
        'KEY_F(10)': 'F10',
        'KEY_F(11)': 'F11',
        'KEY_F(12)': 'F12',
    }


@visidata.VisiData.api
def prettykeys(vd, key):
    if not key:
        return key

    for k, v in vd.prettykeys_trdict.items():
        key = key.replace(k, v)

    # replace ^ with Ctrl but not if ^ is last char
    key = key[:-1].replace('^', 'Ctrl+')+key[-1]
    if key[-1] in string.ascii_uppercase and '+' not in key and '_' not in key:
        key = key[:-1] + 'Shift+' + key[-1]

    return key.strip()
