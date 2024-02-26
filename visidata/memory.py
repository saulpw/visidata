from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict, Column, setitem, ESC

vd.memory = AttrDict()
vd.contexts += [vd.memory]


@VisiData.api
def memo(vd, name, col, row):
    vd.memory[name] = col.getTypedValue(row)
    vd.status('memo %s=%s' % (name, col.getDisplayValue(row)))

@Sheet.api
def memo_cell(sheet):
    if not sheet.cursorCol or not sheet.cursorRow: return
    value_params = dict(prompt='assign value: ', value=sheet.cursorDisplay)
    name_params = dict(prompt='to memo name: ')
    # edits to memo_value are blocked, to preserve its type  #2287
    inputs = vd.inputMultiple(memo_name=name_params,
                              memo_value=value_params,
                              readonly_keys=('memo_value',))
    if not inputs['memo_name']:
        vd.fail('memo name cannot be blank')
    vd.memory[inputs['memo_name']] = sheet.cursorTypedValue
    vd.status(f'memo {inputs["memo_name"]}={sheet.cursorDisplay}')

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


@VisiData.lazy_property
def memosSheet(vd):
    return MemorySheet('memos')


Sheet.addCommand('Alt+Shift+M', 'open-memos', 'vd.push(vd.memosSheet)', 'open the Memory Sheet')
Sheet.addCommand('Alt+m', 'memo-cell', 'memo_cell()', 'store value in current cell in Memory Sheet')
