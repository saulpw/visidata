.. figure:: visidata-interface.png
   :alt: screenshot

   screenshot

-  A. Column names in header row (bold)
-  B. Key columns (highlighted yellow)
-  C. '<'/'>' in header row indicate offscreen columns (dark blue)
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

.. figure:: visidata-interface.png
   :alt: screenshot

   screenshot

-  A. ``Column.name`` (``c_Header``)
-  B. ``keyCols == columns[:nKeys]`` (``c_KeyCols``)
-  C. if
   ``leftVisibleColIndex > nKeys or rightVisibleColIndex < nVisibleCols-1``,
   more non-hidden columns offscreen (``ch_LeftMore``/``ch_RightMore``)
-  onscreen columns:
   ``visibleCols[leftVisibleColIndex:rightVisibleColIndex+1]``
-  D. ``cursorCol == visibleCols[cursorVisibleColIndex]`` (``c_CurCol``)
-  E. (``ch_Ellipsis``)
-  F. ``cursorRow`` (``c_CurRow``)
-  G. ``selectedRows`` (``c_SelectedRow``)
-  H. ``name`` and previous status (``c_StatusLine``)
-  I. ``cursorValue``
-  J. ``VisiData.keystrokes``
-  K. ``nRows``
