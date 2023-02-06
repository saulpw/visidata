'Light-mode theme using 256-colors.'

from visidata import vd

vd.themes['light'] = dict(
        color_default      = 'black on white',  # the default fg and bg colors
        color_key_col      = '20 blue',   # color of key columns
        color_edit_cell    = '234 black',     # cell color to use when editing cell
        color_selected_row = '164 magenta',  # color of selected rows
        color_note_row     = '164 magenta',  # color of row note on left edge
        color_note_type    = '88 red',  # color of cell note for non-str types in anytype columns
        color_warning      = '202 11 yellow',
        color_add_pending  = '34 green',
        color_change_pending  = '166 yellow',
        plot_colors = '20 red magenta black 28 88 94 99 106'
)

