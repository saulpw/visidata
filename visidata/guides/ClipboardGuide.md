 # Copy, Cut and Paste via the Clipboard

Visidata has an internal clipboard, and it can also copy data to and from the
system clipboard.

Note that the system clipboard command can be configured with the
{help.options.clipboard_copy_cmd}


## The Visidata clipboard

Use the [:keys]x[/], [:keys]y[/] and [:keys]p[/] keys with the Visidata
clipboard for cut, copy and paste.

## Copy, cut and paste rows from the Visidata clipboard

- {help.commands.copy_row}
- {help.commands.copy_selected}

- {help.commands.cut_row}
- {help.commands.cut_selected}

- {help.commands.paste_after}
- {help.commands.paste_before}

## Copy, cut and paste cells from the Visidata clipboard

- {help.commands.copy_cell}
- {help.commands.cut_cell}
- {help.commands.paste_cell}

## Copy, and cut columns from the Visidata clipboard

- {help.commands.copy_cells}
- {help.commands.cut_cells}

## Paste columns from the Visidata clipboard

This next command pastes the clipboard into the selected cells in the current
column. If only one value was copied, then it will be repeated. Otherwise, each
of the values from the clipboard will be pasted. If there are fewer values in
the clipboard than in the selected target column, the clipboard values will be
repeated in sequence, e.g. 1,2,3,1,2.

- {help.commands.setcol_clipboard}

## The system clipboard

use [:key]Shift-Y[/] for the system clipboard

## Copy to the system clipboard

- {help.commands.syscopy_cell}
- {help.commands.syscopy_cells}

- {help.commands.syscopy_row}
- {help.commands.syscopy_selected}

## Paste from the system clipboard

- {help.commands.syspaste_cells}
- {help.commands.syspaste_cells_selected}

## Paste a new sheet from the system clipboard

Use the command below to create a new sheet from the data in the system
clipboard. The paste command will prompt for the filetype, so input data can be
in any supported format.

- {help.commands.open_syspaste}


