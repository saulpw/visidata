from visidata import globalCommand, Sheet, TextSheet, vd, error, stacktrace, Command


globalCommand('error-recent', '^E', 'vd.lastErrors and vd.push(ErrorSheet("last_error", vd.lastErrors[-1])) or error("no error")')
globalCommand('errors-all', 'g^E', 'vd.push(ErrorSheet("last_errors", sum(vd.lastErrors[-10:], [])))')

Sheet.addCommand('error-cell', 'z^E', 'vd.push(ErrorSheet("cell_error", getattr(cursorCell, "error", None) or error("no error this cell")))')


class ErrorSheet(TextSheet):
    pass
