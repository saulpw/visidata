from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict, Column, setitem

vd.memory = AttrDict()
vd.contexts += [vd.memory]


@VisiData.api
def memo(vd, name, col, row):
    vd.memory[name] = col.getTypedValue(row)
    vd.status('memo %s=%s' % (name, col.getDisplayValue(row)))


class MemorySheet(Sheet):
    rowtype = 'memos' # rowdef: keys into vd.memory
    columns = [
        Column('name', getter=lambda c,r: r, setter=lambda c,r,v: setitem(vd.memory, v, vd.memory[r])),
        Column('value', getter=lambda c,r: vd.memory[r], setter=lambda c,r,v: setitem(vd.memory, r, v)),
    ]

    @property
    def rows(self):
        return list(vd.memory.keys())

    @rows.setter
    def rows(self, v):
        pass


vd.memosSheet = MemorySheet('memos')


Sheet.addCommand('^[M', 'open-memos', 'vd.push(vd.memosSheet)', 'open the Memory Sheet')
Sheet.addCommand('^[m', 'memo-cell', 'vd.memory[input("assign "+cursorCol.getDisplayValue(cursorRow)+" to: ")] = cursorCol.getTypedValue(cursorRow)', 'store value in current cell in Memory Sheet')
