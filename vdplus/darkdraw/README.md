# DarkDraw II

A terminal-based drawing tool with support for Unicode and 256-color terminals.

Features:
  - user-definable character palettes
  - mixed half- and full- width unicode characters supported
  - extensive unicode discovery sheet
  - manipulate the data behind the drawing

## Commands

- `Ctrl+S` (save-sheet): save drawing to .ddw (either from drawing or backing sheet)
- `Shift+A` (new-drawing): open blank untitled drawing

## Backing sheet

The drawing is rendered from a straightforward list of items with x/y/text/color and other attributes.
This list can be used directly and called the 'backing sheet'.

- `` ` `` (open-source): push backing sheet (if on drawing) or drawing (if on backing sheet)

- `Enter` (dive-cursor): push backing subsheet with only rows under the cursor
  - Note: edits to rows on any backing subsheets will be applied directly, but deleting rows or adding new rows will have no effect.  Any adding, deleting, or reordering must be done from the top sheet.
- `g Enter` (dive-selected): push backing sheet with all selected rows.
- `z Enter` (dive-cursor-group): push backing sheet with rows in the group(s) under the cursor.

### Movement

- `zh` `zj` `zk` `zl`: move the cursor to the next object in that direction.  Useful for sparse areas.
- `g` Arrow (or `gh/gj/gk/gl`): move all the way to the left/bottom/top/right of the drawing

### Cursor

- `Ctrl+Arrow` / `z Arrow`:  expand or contract the cursor box by one cell
- `gz Left` / `gz Up`: contract cursor to minimum width/height


### Selection

- `s` `t` `u`: select/toggle/unselect all items at cursor
- `gs` `gt` `gu`: select/toggle/unselect all items in drawing
- `zs` (select-top-cursor): select only top item at cursor

- `,` (select-equal-char): select all items with the same text as the top item at the cursor

- `{` / `}` (go-prev-selected/go-next-selected): go to prev/next selected item on drawing (same as VisiData sheets)

#### Tags

- `gm` (tag-selected): add given tag to selected items
- `|` (select-tag): select all items with the given tag
- `\\` (unselect-tag): unselect all items with the given tag

### Extra hotkeys

- `v` (): cycles through 3 "visibility modes":
  - 0: don't show extra hotkeys
  - 1: show tag hotkeys
  - 2: show clipboard hotkeys

In visibility mode 1, tags are shown on the right side.
Press the two-digit number (e.g. `01`) before the tag to hide/unhide objects in that tag.
Use `g01` to select and `z01` to unselect objects with that tag.  Press `00` to unhide all tags.

These extra hotkeys will function regardless of whether they are currently shown.

### Character positioning

- `Shift+H/J/K/L` slide the selected items one cell in the given direction
- `g Home` / `g End` send selected rows to the 'top' or 'bottom' of the drawing, by changing their position in the underlying DrawingSheet
- `i` (insert-row): insert a new line at the cursor
- `zi` (insert-col): insert a new column at the cursor

### Editing

- `a` (add-input): add text at the cursor (typing it directly)
- `e` (edit-char): change text of the top cursor item to input
- `ge` (edit-selected): change text all selected characters to input
- `d` (delete-cursor): delete all items under the cursor
- `gd` (delete-selected): delete all selected items

### Clipboard (copy/paste)

- `y` (yank-char): yank items at cursor to clipboard
- `gy` (yank-selected): yank all selected items to clipboard
- `x` (cut-char): delete all chars at cursor and move to clipboard (shortcut for `yd`)
- `zx` (cut-char-top): delete top character at cursor and move to clipboard

- `;` (cycle-paste-mode): cycle between the three paste modes:
  - **all**: the character and its color are pasted as a new item
  - **char**:  the character is pasted as a new item, with the default color (whatever color the paste item had is ignored)
  - **color**:  existing characters are recolored with the paste color

- `p` (paste-chars): paste items on clipbard at cursor according to paste mode (above)

- `zp` (paste-group): paste **reference** to group on clipboard at cursor.

- Individual objects that were copied to the clipboard (with `gy`, for instance) are
available to be pasted onto the drawing with the number keys.  In visibility mode 2, the objects on the clipboard are shown next to a number.  Press that number key to paste that object at the cursor.


### Glyph Discovery

- `Shift+M` to open a unicode browser
   - use standard VisiData commands (`/` to search in a column, `|` to select, `"` to pull selected into their own sheet, etc)
   - and `y` or `gy` to copy characters to the clipboard
   - which can then be `p`asted directly into a Drawing

### Color

- `c` (set-default-color): set default color to color of top item at cursor
- `gc` (set-color-input): set default color to input color
- or, edit the color field directly on the backing sheet
   - all the standard bulk VisiData editing commands are available on the backing sheet

#### Color values

Color values are strings like `'<attr> <fgcolorname> on <bgcolorname>'`.  Any of these may be omitted; order does not matter.  "fg" and "bg" are accepted also.

- color names can be standard terminal colors (`red` `green` `blue` `yellow` `cyan` `magenta` `white` `black`) or a number from 0-255 for [xterm 256 colors]().
- The terminal attributes "underline" and/or "bold" can be anywhere in the string.
- Omitting the fg or bg color will fall back to the default color (white for fg, black for bg) for display.

- Examples:
  - `magenta`
  - `green on black`
  - `fg cyan bg white`
  - `bold 36 on 243'
  - `underline on yellow fg 57'

#### Commands
### Groups

Groups are handled as a single entity, both on the drawing and on the backing sheet.

- `Shift+G` (group-selected): 
- `g Shift+G` (regroup-selected):
- `z Shift+G` (degroup-selected-temp):
- `gz Shift+G` (degroup-selected-perm):

### Animation

If an object or group has its 'frame' attribute set, it will only be drawn in frames with that id.

- `Shift+F` (open-frames): open list of the Frames in this Drawing
- `[` (prev-frame) and `]` (next-frame): go to previous or next frame
- `g[` (first-frame) and `g]` (last-frame): go to first or last frame
- `z[` (new-frame-before) and `z]` (new-frame-after): create a new frame right before or right after the current frame

- `r` (reset-time): replay the animation

### VisiData commands (not specific to DarkDraw)

- `o`: open a new file (open a Drawing if extension is .ddw)
- `Shift+Z`: split window into 50% top and 50% bottom pane
- `z Shift+Z`: split window to specified percent (negative swaps panes)
- `g Shift+Z`: unsplit pane (fullscreen current sheet)

### Notes for VisiData users

- on DrawingSheet, `[` and `]` are unbound (normally sort): accidentally sorting a DrawingSheet can be disastrous, since characters are drawn in order (so later characters are 'on top')
