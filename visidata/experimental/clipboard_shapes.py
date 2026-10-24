'''Copy and paste bindings where the second key is the shape of the target.

`y` (yank) and `p` (paste) become prefixes, followed by a shape:
`.` for a cell, `-` for a row, `|` for a column.  An `s` before the shape
means the selected rows.  Proposed by @midichef in #3008.

Enable in .visidatarc with `import visidata.experimental.clipboard_shapes`.
'''

from visidata import vd, Sheet

Sheet.unbindkey('y')
Sheet.unbindkey('p')
vd.allPrefixes += ['y', 'p', 'ys', 'ps']

Sheet.bindkey('y.',  'copy-cell')         # zy
Sheet.bindkey('y-',  'copy-row')          # y
Sheet.bindkey('ys-', 'copy-selected')     # gy
Sheet.bindkey('ys|', 'copy-cells')        # gzy
Sheet.bindkey('p.',  'paste-cell')        # zp
Sheet.bindkey('p-',  'paste-after')       # p
Sheet.bindkey('ps|', 'setcol-clipboard')  # gzp
