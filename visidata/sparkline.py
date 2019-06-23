from visidata import *


class SparklineColumn(Column):
    def __init__(self, name, **kwargs):
        super().__init__(name, **kwargs)

    def calcValue(self, rows):
        return self.sparkline(*rows)

    def sparkline(self, *values):
        lines = "▁▂▃▄▅▆▇█"
        values = [int(v) for v in values]
        mx = max(values)
        mn = min(values)
        w = (mx - mn) / len(lines)
        bounds = [(mn + w * i) for i in range(len(lines))]

        output = ''
        for val in values:
            for b in bounds:
                if val < b:
                    output += lines[bounds.index(b) - 1]
                    break
            else:
                output += max(lines)
        return output

Sheet.addCommand(None, 'addcol-sparkline', 'addColumn(SparklineColumn("sparkline", type=str))')
