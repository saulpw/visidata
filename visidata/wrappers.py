'value wrappers for nulls and errors'

import copy
import functools

from visidata import options, stacktrace, option

__all__ = ['isNullFunc', 'forward', 'wrmap', 'wrapply', 'TypedWrapper', 'TypedExceptionWrapper']

option('null_value', None, 'a value to be counted as null', replay=True)

def isNullFunc():
    return lambda v,nulls=set([None, options.null_value]): v in nulls or isinstance(v, TypedWrapper)


@functools.total_ordering
class TypedWrapper:
    def __init__(self, func, *args):
        self.type = func
        self.args = args
        self.val = args[0] if args else ''

    def __bool__(self):
        return False

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
        if val is None:
            return TypedWrapper(func, None)
        elif isinstance(val, TypedExceptionWrapper):
            tew = copy.copy(val)
            tew.forwarded = True
            return tew
        elif isinstance(val, TypedWrapper):
            return val
        elif isinstance(val, Exception):
            return TypedWrapper(func, *args)

    try:
        return func(*args, **kwargs)
    except Exception as e:
        e.stacktrace = stacktrace()
        return TypedExceptionWrapper(func, *args, exception=e)
