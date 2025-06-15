import traceback
import sys
import re

from visidata import vd, VisiData

vd.option('debug', False, 'exit on error and display stacktrace')


class ExpectedException(Exception):
    'Controlled Exception from fail() or confirm().  Status or other interface update is done by raiser.'
    pass


def stacktrace(e=None, exclude_caller=False):
    '''Return a list of strings for the stack trace, without newlines
    at the end. If an exception handler is executing, and *e* is none,
    the stack trace includes extra levels of callers beyond the level
    where the exception was caught. If *exclude_caller* is True, the
    trace will exclude the function that called stacktrace(). The
    trace will exclude several uninformative levels that are run
    in interactive visidata.'''

    if e:
        return traceback.format_exception_only(type(e), e)
    #in Python 3.11 we can replace sys.exc_info() with sys.exception()
    handling = (sys.exc_info() != (None, None, None))

    stack = ''.join(traceback.format_stack()).strip().splitlines()

    if handling:
        trim_levels = 2       # remove levels for stacktrace() -> format_stack()
        if exclude_caller:
            trim_levels += 1
        trace_above = stack[:-2*trim_levels]
    else:
        trace_above = stack
    if trace_above:
        trace_above[0] = '  ' + trace_above[0]  #fix indent level of first line
    try:
        # remove several levels of uninformative stacktrace in typical interactive vd
        idx = trace_above.index('    ret = vd.mainloop(scr)')
        trace_above = trace_above[idx+1:]
    except ValueError:
        pass
    if not handling:
        return trace_above
    # remove lines that mark error columns with carets and sometimes tildes
    trace_below = [ line for line in traceback.format_exc().strip().splitlines() if not re.match('^ *~*\\^+$', line) ]
    # move the "Traceback (most recent call last) header to the top of the output
    return [trace_below[0]] + trace_above + trace_below[1:]


@VisiData.api
def exceptionCaught(vd, exc=None, status=True, **kwargs):
    'Add *exc* to list of last errors and add to status history.  Show on left status bar if *status* is True.  Reraise exception if options.debug is True.'
    if isinstance(exc, ExpectedException):  # already reported, don't log
        return
    # save a stack trace that does not include this function
    vd.lastErrors.append(stacktrace(exclude_caller=True))
    if status:
        vd.status(f'{type(exc).__name__}: {exc}', priority=2)
    else:
        vd.addToStatusHistory(vd.lastErrors[-1][-1])
    if vd.options.debug:
        raise


vd.addGlobals(stacktrace=stacktrace, ExpectedException=ExpectedException)

# see textsheet.py for ErrorSheet and associated commands
