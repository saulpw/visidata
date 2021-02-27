from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict, Column, setitem


@VisiData.lazy_property
def memory(vd):
    return AttrDict()

vd.contexts += [vd.memory]

@VisiData.property
def memoriesSheet(vd):
    return MemorySheet("memories")


class MemorySheet(Sheet):
    rowtype = 'memories' # rowdef: keys into vd.memory
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


Sheet.addCommand('^[M', 'open-memory', 'vd.push(vd.memoriesSheet)')
Sheet.addCommand('^[m', 'memorize-cell', 'vd.memory[input("assign "+cursorCol.getDisplayValue(cursorRow)+" to: ")] = cursorCol.getTypedValue(cursorRow)')
