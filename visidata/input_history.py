from visidata import vd, VisiData, Sheet, ItemColumn, asyncthread


vd._inputHistoryList = vd.StoredList(name='input_history')
vd.inputHistory = {}   # [input_type][input] -> anything


@VisiData.api
def addInputHistory(vd, input:str, type:str=''):
    r = vd.processInputHistory(input, type)
    if r:
        vd._inputHistoryList.append(r)


@VisiData.api
def processInputHistory(vd, input:str, type:str=''):
    hist = list(vd.inputHistory.setdefault(type, {}).keys())
    if hist and hist[-1] == input:
        return
    if input in vd.inputHistory[type]:
        n = vd.inputHistory[type][input].get('n', 0)
        del vd.inputHistory[type][input]  # make it the most recent entry
    else:
        n = 0

    r = dict(type=type, input=input, n=n+1)
    vd.inputHistory[type][input] = r
    return r


class InputHistorySheet(Sheet):
    # rowdef: dict(type=, input=, n=)
    # .source=vd.inputHistory
    columns = [
        ItemColumn('type'),
        ItemColumn('input'),
    ]
    def iterload(self):
        yield from vd._inputHistoryList


@VisiData.before
@asyncthread
def run(vd, *args, **kwargs):
    vd._inputHistoryList.reload()
    for x in vd._inputHistoryList:
        vd.processInputHistory(x.input, x.type)


@VisiData.property
def inputHistorySheet(vd):
    return InputHistorySheet('input_history', source=vd._inputHistoryList.path)


vd.addCommand(None, 'open-input-history', 'vd.push(inputHistorySheet)', 'open sheet with previous inputs')
