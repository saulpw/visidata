from visidata import bindkey, BaseSheet

BaseSheet.bindkey('h', 'go-left'),
BaseSheet.bindkey('j', 'go-down'),
BaseSheet.bindkey('k', 'go-up'),
BaseSheet.bindkey('l', 'go-right'),
BaseSheet.bindkey('^F', 'next-page'),
BaseSheet.bindkey('^B', 'prev-page'),
BaseSheet.bindkey('gg', 'go-top'),
BaseSheet.bindkey('G',  'go-bottom'),
BaseSheet.bindkey('gj', 'go-bottom'),
BaseSheet.bindkey('gk', 'go-top'),
BaseSheet.bindkey('gh', 'go-leftmost'),
BaseSheet.bindkey('gl', 'go-rightmost')

BaseSheet.addCommand('^^', 'prev-sheet', 'vd.sheets[1:] or fail("no previous sheet"); vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]')
