from visidata import globalCommand, Sheet, TextSheet, vd, error, stacktrace


globalCommand('^E', 'error-recent', 'vd.lastErrors and vd.push(ErrorSheet("last_error", vd.lastErrors[-1])) or status("no error")')
globalCommand('g^E', 'errors-all', 'vd.push(ErrorSheet("last_errors", sum(vd.lastErrors[-10:], [])))')

Sheet.addCommand('z^E', 'error-cell', 'vd.push(ErrorSheet("cell_error", getattr(cursorCell, "error", None) or fail("no error this cell")))')

class ErrorSheet(TextSheet):
    pass
