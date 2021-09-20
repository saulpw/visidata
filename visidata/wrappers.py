'value wrappers for nulls and errors'

from copy import copy
import functools

from visidata import options, stacktrace, BaseSheet, vd

__all__ = ['forward', 'wrmap', 'wrapply', 'TypedWrapper', 'TypedExceptionWrapper']

vd.option('null_value', None, 'a value to be counted as null', replay=True)

@BaseSheet.api
def isNullFunc(sheet):
    'Return func(value) which returns whether or not *value* is null.'
    nullv = sheet.options.null_value
    if nullv is None:
        return lambda v: v is None or isinstance(v, TypedWrapper)
    return lambda v, nullv=nullv: v is None or v == nullv or isinstance(v, TypedWrapper)


@functools.total_ordering
class TypedWrapper:
    def __init__(self, func, *args):
        self.type = func
        self.args = args
        self.val = args[0] if args else ''

    def __bool__(self):
        return False

    def __len__(self):
        return 0

    def __str__(self):
        return '%s(%s)' % (self.type.__name__, ','.join(str(x) for x in self.args))

    def __lt__(self, x):
        'maintain sortability; wrapped objects are always least'
        return True

    def __add__(self, x):
        return x

    def __radd__(self, x):
        return x

    def __hash__(self):
        return hash((self.type, str(self.val)))

    def __eq__(self, x):
        if isinstance(x, TypedWrapper):
            return self.type == x.type and self.val == x.val

    def __iter__(self):
        return self
    def __next__(self):
        raise StopIteration

class TypedExceptionWrapper(TypedWrapper):
    def __init__(self, func, *args, exception=None):
        TypedWrapper.__init__(self, func, *args)
        self.exception = exception
        self.stacktrace = stacktrace()
        self.forwarded = False

    def __str__(self):
        return str(self.exception)

    def __hash__(self):
        return hash((type(self.exception), ''.join(self.stacktrace[:-1])))

    def __eq__(self, x):
        if isinstance(x, TypedExceptionWrapper):
            return type(self.exception) is type(x.exception) and self.stacktrace[:-1] == x.stacktrace[:-1]


def forward(wr):
    if isinstance(wr, TypedExceptionWrapper):
        wr.forwarded = True
    return wr


def wrmap(func, iterable, *args):
    'Same as map(func, iterable, *args), but ignoring exceptions.'
    for it in iterable:
        try:
            yield func(it, *args)
        except Exception as e:
            pass


def wrapply(func, *args, **kwargs):
    'Like apply(), but which wraps Exceptions and passes through Wrappers (if first arg)'
    if args:
        val = args[0]
        if val is None:  # None values propagate to TypedWrappers
            return TypedWrapper(func, None)
        elif isinstance(val, TypedExceptionWrapper):  # previous Exceptions propagate, marked 'forwarded'
            tew = copy(val)
            tew.forwarded = True
            return tew
        elif isinstance(val, TypedWrapper):  # TypedWrappers (likely None, from above) propagate
            return val
        elif isinstance(val, Exception):  # Exception values become TypedWrappers
            return TypedWrapper(func, *args)

    try:
        return func(*args, **kwargs)
    except Exception as e:
        e.stacktrace = stacktrace()
        return TypedExceptionWrapper(func, *args, exception=e)
