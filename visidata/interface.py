from visidata import vd


vd.option('disp_splitwin_pct', 0, 'height of second sheet on screen')
vd.option('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
vd.option('disp_truncator', '…', 'indicator that the contents are only partially visible')
vd.option('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
vd.option('disp_more_left', '<', 'header note indicating more columns to the left')
vd.option('disp_more_right', '>', 'header note indicating more columns to the right')
vd.option('disp_error_val', '', 'displayed contents for computation exception')
vd.option('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

vd.option('disp_pending', '', 'string to display in pending cells')
vd.option('note_pending', '⌛', 'note to display for pending cells')
vd.option('note_format_exc', '?', 'cell note for an exception during formatting')
vd.option('note_getter_exc', '!', 'cell note for an exception during computation')
vd.option('note_type_exc', '!', 'cell note for an exception during type conversion')

vd.option('color_note_pending', 'bold magenta', 'color of note in pending cells')
vd.option('color_note_type', '226 yellow', 'color of cell note for non-str types in anytype columns')
vd.option('color_note_row', '220 yellow', 'color of row note on left edge')
vd.option('scroll_incr', -3, 'amount to scroll with scrollwheel')
vd.option('disp_column_sep', '│', 'separator between columns')
vd.option('disp_keycol_sep', '║', 'separator between key columns and rest of columns')
vd.option('disp_rowtop_sep', '│', '') # ╷│┬╽⌜⌐▇
vd.option('disp_rowmid_sep', '⁝', '') # ┃┊│█
vd.option('disp_rowbot_sep', '⁝', '') # ┊┴╿⌞█⍿╵⎢┴⌊  ⋮⁝
vd.option('disp_rowend_sep', '║', '') # ┊┴╿⌞█⍿╵⎢┴⌊
vd.option('disp_keytop_sep', '║', '') # ╽╿┃╖╟
vd.option('disp_keymid_sep', '║', '') # ╽╿┃
vd.option('disp_keybot_sep', '║', '') # ╽╿┃╜‖
vd.option('disp_endtop_sep', '║', '') # ╽╿┃╖╢
vd.option('disp_endmid_sep', '║', '') # ╽╿┃
vd.option('disp_endbot_sep', '║', '') # ╽╿┃╜‖
vd.option('disp_selected_note', '•', '') #
vd.option('disp_sort_asc', '↑↟⇞⇡⇧⇑', 'characters for ascending sort') # ↑▲↟↥↾↿⇞⇡⇧⇈⤉⤒⥔⥘⥜⥠⍏˄ˆ
vd.option('disp_sort_desc', '↓↡⇟⇣⇩⇓', 'characters for descending sort') # ↓▼↡↧⇂⇃⇟⇣⇩⇊⤈⤓⥕⥙⥝⥡⍖˅ˇ
vd.option('color_default', 'white on black', 'the default fg and bg colors')
vd.option('color_default_hdr', 'bold', 'color of the column headers')
vd.option('color_bottom_hdr', 'underline', 'color of the bottom header row')
vd.option('color_current_row', 'reverse', 'color of the cursor row')
vd.option('color_current_col', 'bold', 'color of the cursor column')
vd.option('color_current_hdr', 'bold reverse', 'color of the header for the cursor column')
vd.option('color_column_sep', '246 blue', 'color of column separators')
vd.option('color_key_col', '81 cyan', 'color of key columns')
vd.option('color_hidden_col', '8', 'color of hidden columns on metasheets')
vd.option('color_selected_row', '215 yellow', 'color of selected rows')
vd.option('color_code', 'bold', 'color of code sample')


vd.option('force_256_colors', False, 'use 256 colors even if curses reports fewer')

vd.option('quitguard', False, 'confirm before quitting modified sheet')
vd.option('default_width', 20, 'default column width', replay=True)   # TODO: make not replay and remove from markdown saver
vd.option('default_height', 4, 'default column height')
vd.option('textwrap_cells', True, 'wordwrap text for multiline rows')
