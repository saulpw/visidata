from visidata import BaseSheet, vd, CompleteKey

@BaseSheet.api
def inputLongname(sheet):
    longnames = set(k for (k, obj), v in vd.commands.iter(sheet))
    return vd.input("command name: ", completer=CompleteKey(sorted(longnames)), type='longname')

@BaseSheet.api
def exec_longname(sheet, longname):
    if not sheet.getCommand(longname):
        vd.warning(f'no command {longname}')
        return
    sheet.execCommand(longname)

vd.addCommand(' ', 'exec-longname', 'exec_longname(inputLongname())', 'execute command by its longname')
