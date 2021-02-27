from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict


@VisiData.lazy_property
def memory(vd):
    return AttrDict()

vd.contexts += [vd.memory]

@Sheet.property
def memories(sheet):
    return MemorySheet("memories")


class MemorySheet(Sheet):
    rowtype = 'memories'
    columns = [
        ItemColumn('name', 0),
        ItemColumn('value', 1),
    ]
    def reload(self):
        self.rows = list(vd.memory.items())


Sheet.addCommand('^[M', 'open-memory', 'vd.push(sheet.memories)')
Sheet.addCommand('^[m', 'memorize-cell', 'vd.memory[input("assign "+cursorCol.getDisplayValue(cursorRow)+" to: ")] = cursorCol.getTypedValue(cursorRow)')
