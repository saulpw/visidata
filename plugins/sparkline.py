from visidata import Column, ColumnsSheet, Sheet, option, options, BaseException


option('disp_sparkline', '▁▂▃▄▅▆▇', 'characters to display sparkline')


class SparklineColumn(Column):

    def calcValue(self, r):
        return self.sparkline(*tuple(c.getTypedValue(r) for c in self.source))

    def sparkline(*values):
        lines = options.disp_sparkline
        values = [v for v in values if isinstance(v, (int, float))]
        mx = max(values)
        mn = min(values)
        w = (mx - mn) / len(lines)
        bounds = [(mn + w * i) for i in range(len(lines))]

        output = ''
        for val in values:
            for b in bounds:
                if mn == 0 and val == 0:
                    output += ' '
                    break
                if val < b:
                    output += lines[bounds.index(b) - 1]
                    break
            else:
                output += max(lines)
        return output


ColumnsSheet.addCommand(None, 'addcol-sparkline', 'cursorRow.sheet.addColumn(SparklineColumn("sparkline", source=selectedRows))')
Sheet.addCommand(None, 'addcol-sparkline', 'addColumn(SparklineColumn("sparkline", source=numericCols(nonKeyVisibleCols)))')
