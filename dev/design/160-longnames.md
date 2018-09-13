# Command longname design and checklist

1) two words max if possible, should be short and fit on a keymap (verb - object - input)

2) command classes should be unique in their first 3 chars and ideally mostly in their first 2.

3) command longnames should be intuitively understandable, or at least not jargony

4) longnames should evoke interface, when possible

definitions:
- syscopy: copy to system clipboard
- sysopen: open with $EDITOR or other external program.  'launch'?
- cells: this column, selected rows (or all rows if none selected)
- expr: python expression
- regex: python regex
- all: all sheets or all visible columns
- col: cursorCol (will be marked in sheet)
- cols: all visible columns
- subst: regex A/B
- capture: regex match A(B) yielding capture groups
- dup: push copy of sheet
- searchr: search reverse
- go: move the cursor
- scroll: change the visible screen area without changing the cursor
- select: all or selected
- fill: (from fill null cells)
- dive: conceptual -> go deeper
- slide: move row/column
- show: displays on status
- cancel-: kill thread/async process
- setcol: set selected cells in this column
- addcol: add new column to this sheet
- search: on default with regex
- aggregate: set an aggregator
- delete: cuts and moves to clipboard

## notes 

- swap-sheet -> was an alt for ^^ but is not technically accurate if we expand the design to allow `3^^` to push the 3rd sheet to the stack; in order to future-proof sticking with prev-sheet or go-sheet
- n/N have prev- as a prefix instead of search bc search- takes an input

- syscopy should not be logged.
- copy needs to be logged, as the copied rows/values can be pasted

## Todo

- commands2md.py catalog of all commands by longname with default keybinding
  - include helpstr
- document how to remap a keybinding by longname
- write tool to test coverage/cohesion of keybindings/longnames/commands.tsv
- Checklist for new and updated commands
- publish list of definitions
- publish keyboard layouts with new longnames (make 3-word longnames fit)
   - clickable keys to go to specific doc section
- change options.cmdlog_longname default to True
- write up our rules and glossary and include them in our www



