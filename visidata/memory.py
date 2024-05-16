from visidata import Sheet, VisiData, ItemColumn, vd, AttrDict, Column, setitem, ESC

vd.memory = AttrDict()
vd.contexts += [vd.memory]


@VisiData.api
def memoValue(vd, name, value, dispvalue):
    vd.memory[name] = value
    vd.status(f'memo {name}={dispvalue}')


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


@VisiData.api
def inputMemoName(vd, value):
    value_params = dict(prompt="assign value: ", value=value)
    name_params = dict(prompt="to memo name: ")
    r = vd.inputMultiple(memo_name=name_params, memo_value=value_params)
    name = r['memo_name']
    if not name:
        vd.fail('memo name cannot be blank')
    return name


Sheet.addCommand('Alt+Shift+M', 'open-memos', 'vd.push(vd.memosSheet)', 'open the Memory Sheet')
Sheet.addCommand('Alt+m', 'memo-cell', 'vd.memoValue(inputMemoName(cursorDisplay), cursorTypedValue, cursorDisplay)', 'store value in current cell to Memory Sheet')
