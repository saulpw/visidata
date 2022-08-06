import traceback

from visidata import vd, VisiData, options

__all__ = ['stacktrace', 'ExpectedException']

class ExpectedException(Exception):
    'Controlled Exception from fail() or confirm().  Status or other interface update is done by raiser.'
    pass


def stacktrace(e=None):
    if not e:
        return traceback.format_exc().strip().splitlines()
    return traceback.format_exception_only(type(e), e)


@VisiData.api
def exceptionCaught(vd, exc=None, status=True, **kwargs):
    'Add *exc* to list of last errors and add to status history.  Show on left status bar if *status* is True.  Reraise exception if options.debug is True.'
    if isinstance(exc, ExpectedException):  # already reported, don't log
        return
    vd.lastErrors.append(stacktrace())
    if status:
        vd.status(f'{type(exc).__name__}: {exc}', priority=2)
    else:
        vd.addToStatusHistory(vd.lastErrors[-1][-1])
    if vd.options.debug:
        raise

# see textsheet.py for ErrorSheet and associated commands
