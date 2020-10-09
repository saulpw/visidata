'''This adds the `unfurl-col` command, to unfurl a column containing iterable values, such as lists, dicts, and strings.
Unfurling pushes a new sheet, with each key/value pair in the unfurled column values getting its own row, with the rest of the source sheet's columns copied for each of those rows.

Note: When unfurling a column, non-iterable objects (such as integers) are treated as single-item lists, so that they too can be unfurled.

Credit to Jeremy Singer-Vine for the idea and original implementation.
'''

from collections.abc import Iterable, Mapping
from visidata import vd, Progress, Sheet, Column, ColumnItem, SettableColumn, SubColumnFunc, asyncthread, clean_to_id


class UnfurledSheet(Sheet):
    @asyncthread
    def reload(self):
        # Copy over base sheet, using SubColumnFunc
        self.columns = []
        for col in self.source.columns:
            if col is self.source_col:
                # Replace iterable column with two columns: keys and values
                self.cursorVisibleColIndex = len(self.columns)-1
                self.addColumn(ColumnItem(col.name + "_key", 1))
                self.addColumn(ColumnItem(col.name + "_value", 2))
            else:
                self.addColumn(SubColumnFunc(col.name, col, 0, keycol=col.keycol))

        self.rows = []
        for row in Progress(self.source.rows):
            val = self.source_col.getValue(row)

            if not isinstance(val, Iterable) or isinstance(val, str):
                val = [ val ]

            if isinstance(val, Mapping):
                gen = val.items()
            else:
                gen = enumerate(val)

            for key, sub_value in gen:
                new_row = [ row, key, sub_value ]
                self.addRow(new_row)


@Sheet.api
def unfurl_col(sheet, col):
    clean_id = clean_to_id(col.name)
    vs = UnfurledSheet(f"{sheet.name}_{clean_id}_unfurled", source=sheet, source_col=col)
    return vs


Sheet.addCommand("zM", "unfurl-col", "vd.push(unfurl_col(cursorCol))", "row-wise expand current column of lists (e.g. [2]) or dicts (e.g. {3}) within that column")
