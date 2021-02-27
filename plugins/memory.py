from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict, Column, setitem


@VisiData.lazy_property
def memory(vd):
    return AttrDict()

vd.contexts += [vd.memory]

@VisiData.property
def memoriesSheet(vd):
    return MemorySheet("memories")


class MemorySheet(Sheet):
    rowtype = 'memories'
    columns = [
        Column('name', getter=lambda c,r: r[0], setter=lambda c,r,v: setitem(vd.memory, v, r[1])),
        Column('value', getter=lambda c,r: r[1], setter=lambda c,r,v: setitem(vd.memory, r[0], v)),
    ]
    def reload(self):
        self.rows = list(vd.memory.items())


Sheet.addCommand('^[M', 'open-memory', 'vd.push(vd.memoriesSheet)')
Sheet.addCommand('^[m', 'memorize-cell', 'vd.memory[input("assign "+cursorCol.getDisplayValue(cursorRow)+" to: ")] = cursorCol.getTypedValue(cursorRow)')
