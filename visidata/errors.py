from visidata import globalCommand, Sheet, TextSheet, vd, error, stacktrace, Command


globalCommand('^E', 'vd.lastErrors and vd.push(ErrorSheet("last_error", vd.lastErrors[-1])) or error("no error")', 'view traceback for most recent error', 'errors-recent')
globalCommand('g^E', 'vd.push(ErrorSheet("last_errors", sum(vd.lastErrors[-10:], [])))', 'view traceback for most recent errors', 'info-errors-all')

Sheet.commands += [
    Command('z^E', 'vd.push(ErrorSheet("cell_error", getattr(cursorCell, "error", None) or error("no error this cell")))', 'view traceback for error in current cell'),
]


class ErrorSheet(TextSheet):
    pass
