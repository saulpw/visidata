from visidata import VisiData, Sheet

@Sheet.api
@VisiData.api
def use_light_colors(obj, flag=True):
    if flag:
        obj.options.color_default      = 'black on white'  # the default fg and bg colors
        obj.options.color_key_col      = '20 blue'   # color of key columns
        obj.options.color_edit_cell    = '234 black'     # cell color to use when editing cell
        obj.options.color_selected_row = '164 magenta'  # color of selected rows
        obj.options.color_note_row     = '164 magenta'  # color of row note on left edge
        obj.options.color_note_type    = '88 red'  # color of cell note for non-str types in anytype columns
        obj.options.plot_colors = '20 red magenta black 28 88 94 99 106'
    else:
        obj.options.unset('color_default')
        obj.options.unset('color_key_col')
        obj.options.unset('color_edit_cell')
        obj.options.unset('color_selected_row')
        obj.options.unset('color_note_row')
        obj.options.unset('color_note_type')
        obj.options.unset('plot_colors')
