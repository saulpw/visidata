from visidata import *


@asyncthread
@VisiData.api
def help_search(vd, sheet, regex):
    vs = HelpSheet(source=None)
    vs.rows = []  # do not trigger push reload
    vd.push(vs)   # push first, then reload
    vd.sync(vs.reload())

    # find rows matching regex on original HelpSheet
    rowidxs = list(vd.searchRegex(vs, regex=regex, columns="visibleCols"))

    # add only matching rows
    allrows = vs.rows
    vs.rows = []
    for rowidx in rowidxs:
        vs.addRow(allrows[rowidx])


globalCommand(None, 'help-search', 'help_search(sheet, input("help: "))')
