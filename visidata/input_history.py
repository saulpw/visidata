from visidata import vd, VisiData, Sheet, ItemColumn


@VisiData.stored_property
def inputHistory(vd):
    return {}  # [input_type][input] -> anything


@VisiData.api
def addInputHistory(vd, input:str, type:str=''):
    hist = list(vd.inputHistory.setdefault(type, {}).keys())
    if hist and hist[-1] == input:
        return
    if input in vd.inputHistory[type]:
        n = vd.inputHistory[type][input]['n']
        del vd.inputHistory[type][input]  # make it the most recent entry
    else:
        n = 0
    vd.inputHistory[type][input] = dict(type=type, input=input, n=n+1)


class InputHistorySheet(Sheet):
    # rowdef: dict(type=, input=, n=)
    # .source=vd.inputHistory
    columns = [
        ItemColumn('type'),
        ItemColumn('input'),
    ]
    def iterload(self):
        for type, inputs in vd.inputHistory.items():
            for v in inputs.values():
                yield v


@VisiData.property
def inputHistorySheet(vd):
    return InputHistorySheet('input_history', source=vd.inputHistory)


vd.addCommand(None, 'open-input-history', 'vd.push(inputHistorySheet)', 'open sheet with previous inputs')
