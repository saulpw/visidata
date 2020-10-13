
# Sheet.memory = Sheet.lazy_property(dict)

class MemorySheet(Sheet):
    rowtype = 'memories'
    columns = [
        Column
    ]
    def reload(self):
        self.rows = self.source.memory

Sheet.addCommand('', 'set-rowtype', 'sheet.rowtype=input("new rowtype: ", value=sheet.rowtype)')
Sheet.addCommand('', 'open-memory', 'vd.push(MemorySheet("memories", source=sheet))')

@Sheet.lazy_property
def memory(sheet):
    return {}


