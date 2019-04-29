from visidata import bindkey, BaseSheet

bindkey('h', 'go-left'),
bindkey('j', 'go-down'),
bindkey('k', 'go-up'),
bindkey('l', 'go-right'),
bindkey('^F', 'next-page'),
bindkey('^B', 'prev-page'),
bindkey('gg', 'go-top'),
bindkey('G',  'go-bottom'),
bindkey('gj', 'go-bottom'),
bindkey('gk', 'go-top'),
bindkey('gh', 'go-leftmost'),
bindkey('gl', 'go-rightmost')

BaseSheet.addCommand('^^', 'prev-sheet', 'vd.sheets[1:] or fail("no previous sheet"); vd.sheets[0], vd.sheets[1] = vd.sheets[1], vd.sheets[0]')
