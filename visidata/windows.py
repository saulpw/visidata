import sys
from visidata import VisiData, vd, ALT

@VisiData.property
def is_windows(vd):
    return sys.platform == 'win32'

if vd.is_windows:
    vd.bindkey('^Z', 'undo-last')

    # keypad
#    vd.bindkey('PAD0', 'KEY_IC')
    vd.bindkey('PADSTOP', 'KEY_DC')
    vd.bindkey('KEY_A1', 'KEY_HOME')
    vd.bindkey('KEY_A2', 'KEY_UP')
    vd.bindkey('KEY_A3', 'KEY_PPAGE')
    vd.bindkey('KEY_B1', 'KEY_LEFT')

    vd.bindkey('KEY_B3', 'KEY_RIGHT')
    vd.bindkey('KEY_C1', 'KEY_END')
    vd.bindkey('KEY_C2', 'KEY_DOWN')
    vd.bindkey('KEY_C3', 'KEY_NPAGE')

    # Alt+F1 instead of Alt+1
    for i in range(12):
        vd.bindkey('KEY_F(%s)'%(i+37), ALT+'%s'%(i+1))

    vd.options.color_key_col = 'cyan'
    vd.options.color_note_type = 'yellow'
    vd.options.color_note_row = 'yellow'
    vd.options.color_selected_row = 'yellow'
