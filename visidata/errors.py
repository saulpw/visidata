import traceback
import re

from visidata import vd, VisiData

vd.option('debug', False, 'exit on error and display stacktrace')


class ExpectedException(Exception):
    'Controlled Exception from fail() or confirm().  Status or other interface update is done by raiser.'
    pass


def stacktrace(e=None):
    '''Return a list of strings. Includes extra callstack levels above the
    level where the exception was technically caught, to aid debugging.'''

    if not e:
        stack = ''.join(traceback.format_stack()).strip().splitlines()
        trim_levels = 3   # calling function -> stacktrace() -> format_stack()
        trace_above = stack[:-2*trim_levels]
        trace_above[0] = '  ' + trace_above[0]  #fix indent level of first line
        try:
            # remove several levels of uninformative stacktrace in typical interactive vd
            idx = trace_above.index('    ret = vd.mainloop(scr)')
            trace_above = trace_above[idx+1:]
        except ValueError:
            pass
        # remove lines that mark error columns with carets and sometimes tildes
        trace_below = [ line for line in traceback.format_exc().strip().splitlines() if not re.match('^ *~*\\^+$', line) ]
        return [trace_below[0]] + trace_above + trace_below[1:]
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


vd.addGlobals(stacktrace=stacktrace, ExpectedException=ExpectedException)

# see textsheet.py for ErrorSheet and associated commands
