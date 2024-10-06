from visidata import VisiData, vd

vd.theme_option('disp_splitwin_pct', 0, 'height of second sheet on screen')
vd.theme_option('disp_note_none', '⌀',  'visible contents of a cell whose value is None')
vd.theme_option('disp_truncator', '…', 'indicator that the contents are only partially visible')
vd.theme_option('disp_oddspace', '\u00b7', 'displayable character for odd whitespace')
vd.theme_option('disp_more_left', '<', 'header note indicating more columns to the left')
vd.theme_option('disp_more_right', '>', 'header note indicating more columns to the right')
vd.theme_option('disp_error_val', '', 'displayed contents for computation exception')
vd.theme_option('disp_ambig_width', 1, 'width to use for unicode chars marked ambiguous')

vd.theme_option('disp_pending', '', 'string to display in pending cells')
vd.theme_option('disp_note_pending', ':', 'note to display for pending cells')
vd.theme_option('disp_note_fmtexc', '?', 'cell note for an exception during formatting')
vd.theme_option('disp_note_getexc', '!', 'cell note for an exception during computation')
vd.theme_option('disp_note_typeexc', '!', 'cell note for an exception during type conversion')

vd.theme_option('color_note_pending', 'bold green', 'color of note in pending cells')
vd.theme_option('color_note_type', '226 yellow', 'color of cell note for non-str types in anytype columns')
vd.theme_option('color_note_row', '220 yellow', 'color of row note on left edge')
vd.option('scroll_incr', -3, 'amount to scroll with scrollwheel')
vd.theme_option('disp_column_sep', '│', 'separator between columns')
vd.theme_option('disp_keycol_sep', '║', 'separator between key columns and rest of columns')
vd.theme_option('disp_rowtop_sep', '│', '') # ╷│┬╽⌜⌐▇
vd.theme_option('disp_rowmid_sep', '⁝', '') # ┃┊│█
vd.theme_option('disp_rowbot_sep', '⁝', '') # ┊┴╿⌞█⍿╵⎢┴⌊  ⋮⁝
vd.theme_option('disp_rowend_sep', '║', '') # ┊┴╿⌞█⍿╵⎢┴⌊
vd.theme_option('disp_keytop_sep', '║', '') # ╽╿┃╖╟
vd.theme_option('disp_keymid_sep', '║', '') # ╽╿┃
vd.theme_option('disp_keybot_sep', '║', '') # ╽╿┃╜‖
vd.theme_option('disp_endtop_sep', '║', '') # ╽╿┃╖╢
vd.theme_option('disp_endmid_sep', '║', '') # ╽╿┃
vd.theme_option('disp_endbot_sep', '║', '') # ╽╿┃╜‖
vd.theme_option('disp_selected_note', '•', '') #
vd.theme_option('disp_sort_asc', '↑↟⇞⇡⇧⇑', 'characters for ascending sort') # ↑▲↟↥↾↿⇞⇡⇧⇈⤉⤒⥔⥘⥜⥠⍏˄ˆ
vd.theme_option('disp_sort_desc', '↓↡⇟⇣⇩⇓', 'characters for descending sort') # ↓▼↡↧⇂⇃⇟⇣⇩⇊⤈⤓⥕⥙⥝⥡⍖˅ˇ
vd.theme_option('color_default', 'white on black', 'the default fg and bg colors')
vd.theme_option('color_default_hdr', 'bold white on black', 'color of the column headers')
vd.theme_option('color_bottom_hdr', 'underline white on black', 'color of the bottom header row')
vd.theme_option('color_current_row', 'reverse', 'color of the cursor row')
vd.theme_option('color_current_col', 'bold on 232', 'color of the cursor column')
vd.theme_option('color_current_cell', '', 'color of current cell, if different from color_current_row+color_current_col')
vd.theme_option('color_current_hdr', 'bold reverse', 'color of the header for the cursor column')
vd.theme_option('color_column_sep', 'white on black', 'color of column separators')
vd.theme_option('color_key_col', '81 cyan', 'color of key columns')
vd.theme_option('color_hidden_col', '8', 'color of hidden columns on metasheets')
vd.theme_option('color_selected_row', '215 yellow', 'color of selected rows')
vd.theme_option('color_clickable', 'bold', 'color of internally clickable item')
vd.theme_option('color_code', 'bold white on 237', 'color of code sample')
vd.theme_option('color_heading', 'bold black on yellow', 'color of header')
vd.theme_option('color_guide_unwritten', '243 on black', 'color of unwritten guides in GuideGuide')

vd.theme_option('force_256_colors', False, 'use 256 colors even if curses reports fewer')

vd.option('quitguard', False, 'confirm before quitting modified sheet')
vd.option('default_width', 20, 'default column width', replay=True)   # TODO: make not replay and remove from markdown saver
vd.option('default_height', 4, 'default column height')
