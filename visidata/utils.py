import operator
import string
import re

'Various helper classes and functions.'

__all__ = ['AlwaysDict', 'AttrDict', 'moveListItem', 'namedlist', 'classproperty', 'cleanName', 'MissingAttrFormatter']


class AlwaysDict(dict):
    'return same val for all keys'
    def __init__(self, val, **kwargs):
        super().__init__(**kwargs)
        self._val = val

    def __getitem__(self, k):
        return self._val

class AttrDict(dict):
    'Augment a dict with more convenient .attr syntax.  not-present keys return None.'
    def __getattr__(self, k):
        try:
            v = self[k]
            if isinstance(v, dict) and not isinstance(v, AttrDict):
                v = AttrDict(v)
            return v
        except KeyError:
            if k.startswith("__"):
                raise AttributeError
            return None

    def __setattr__(self, k, v):
        self[k] = v

    def __dir__(self):
        return self.keys()


class classproperty(property):
    def __get__(self, cls, obj):
        return classmethod(self.fget).__get__(None, obj or cls)()


def moveListItem(L, fromidx, toidx):
    "Move element within list `L` and return element's new index."
    toidx = min(max(toidx, 0), len(L)-1)
    fromidx = min(max(fromidx, 0), len(L)-1)
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx


def cleanName(s):
    s = re.sub(r'[^\w\d_]', '_', s)  # replace non-alphanum chars with _
    s = re.sub(r'_+', '_', s)  # replace runs of _ with a single _
    s = s.strip('_')
    return s


class OnExit:
    '"with OnExit(func, ...):" calls func(...) when the context is exited'
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            vd.exceptionCaught(e)


def itemsetter(i):
    def g(obj, v):
        obj[i] = v
    return g


def namedlist(objname, fieldnames):
    'like namedtuple but editable'
    class NamedListTemplate(list):
        __name__ = objname
        _fields = fieldnames

        def __init__(self, L=None, **kwargs):
            if L is None:
                L = [None]*len(self._fields)
            elif len(L) < len(self._fields):
                L.extend([None]*(len(self._fields) - len(L)))
            super().__init__(L)
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __getattr__(self, k):
            'to enable .fieldname'
            try:
                return self[self._fields.index(k)]
            except ValueError:
                raise AttributeError

        def __setattr__(self, k, v):
            'to enable .fieldname ='
            try:
                self[self._fields.index(k)] = v
            except ValueError:
                super().__setattr__(k, v)

    return NamedListTemplate

class MissingAttrFormatter(string.Formatter):
    "formats {} fields with `''`, that would normally result in a raised KeyError or AttributeError; intended for user customisable format strings."
    def get_field(self, field_name, *args, **kwargs):
        try:
            return super().get_field(field_name, *args, **kwargs)
        except (KeyError, AttributeError):
            return (None, field_name)

    def format_field(self, value, format_spec):
        # value is missing
        if value is None:
            return ''
        elif not value:
            return str(value)
        return super().format_field(value, format_spec)
