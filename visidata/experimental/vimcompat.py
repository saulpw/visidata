"""Additional vim-like bindings for Visidata

Enable in .visidatarc with `import visidata.experimental.vimcompat`.
"""

from visidata import BaseSheet

# Jump to first row and column with 'go'
BaseSheet.bindkey('go', 'go-home')

# standard half-page movement
BaseSheet.bindkey('Ctrl+D', 'go-pagedown-half')
BaseSheet.bindkey('Ctrl+U', 'go-pageup-half')
