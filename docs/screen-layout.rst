.. figure:: https://raw.githubusercontent.com/saulpw/visidata/stable/docs/img/visidata-interface.png
   :alt: screenshot

-  A. Column names in header row (bold)
-  B. Key columns (blue)
-  C. '<'/'>' in header row indicate offscreen columns
-  D. Current column (bold with inverse header)
-  E. Overflowing cells truncated with ellipsis (``…``)
-  F. Row cursor (inverse row)
-  G. Selected rows (green)
-  H. Sheet name and status line (lower left)
-  I. Current cell at intersection of current row and current column
-  J. Previously pressed keystrokes (lower right)
-  K. Number of rows in sheet (lower right)

For developers
--------------

.. figure:: https://raw.githubusercontent.com/saulpw/visidata/stable/docs/img/visidata-interface.png
   :alt: screenshot

-  A. ``Column.name`` (``color_default_hdr``)
-  B. ``keyCols == columns[:nKeys]`` (``color_key_col``)
-  C. if
   ``leftVisibleColIndex > nKeys or rightVisibleColIndex < nVisibleCols-1``,
   more non-hidden columns offscreen (``disp_more_left``/``disp_more_right``)
-  onscreen columns:
   ``visibleCols[leftVisibleColIndex:rightVisibleColIndex+1]``
-  D. ``cursorCol == visibleCols[cursorVisibleColIndex]`` (``color_current_col``)
-  E. (``disp_truncator``)
-  F. ``cursorRow`` (``color_current_row``)
-  G. ``selectedRows`` (``color_selected_row``)
-  H. ``name`` and previous status (``color_status``)
-  I. ``cursorValue``
-  J. ``VisiData.keystrokes``
-  K. ``nRows``
