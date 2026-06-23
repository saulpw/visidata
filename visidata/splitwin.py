from visidata import VisiData, BaseSheet, vd

vd.theme_option('disp_splitwin_pct', 0, 'height of second sheet on screen')

vd.activePane = 1   # pane numbering starts at 1; pane 0 means active pane
BaseSheet.init('pane', lambda: 1)


@BaseSheet.api
def splitPane(sheet, pct=None):
    if vd.activeStack[1:]:
        undersheet = vd.activeStack[1]
        pane = 1 if undersheet.pane == 2 else 2
        vd.push(undersheet, pane=pane)
        vd.activePane = pane

    vd.options.disp_splitwin_pct = pct


@VisiData.api
def splitwin_close(vd):
    vd.options.disp_splitwin_pct = 0
    for vs in vd.stackedSheets:
        vs.pane = 1
        vd.activePane = 1


BaseSheet.addCommand('Z', 'splitwin-half', 'splitPane(vd.options.disp_splitwin_pct or 50)', 'ensure split pane is set and push under sheet onto other pane')
BaseSheet.addCommand('gZ', 'splitwin-close', 'vd.splitwin_close()', 'close split screen')
BaseSheet.addCommand('Tab', 'splitwin-swap', 'vd.activePane = 1 if sheet.pane == 2 else 2', 'jump to inactive pane')
BaseSheet.addCommand('gTab', 'splitwin-swap-pane', 'vd.options.disp_splitwin_pct=-vd.options.disp_splitwin_pct', 'swap panes onscreen')
BaseSheet.addCommand('zZ', 'splitwin-input', 'vd.options.disp_splitwin_pct = input("% height for split window: ", value=vd.options.disp_splitwin_pct)', 'set split pane to specific size')

vd.addMenuItems('''
    View > Split pane > in half > splitwin-half
    View > Split pane > in percent > splitwin-input
    View > Split pane > unsplit > splitwin-close
    View > Split pane > swap panes > splitwin-swap-pane
    View > Split pane > goto other pane > splitwin-swap
''')
