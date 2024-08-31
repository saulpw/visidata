from contextlib import contextmanager
import operator
import string
import re

'Various helper classes and functions.'

__all__ = ['AlwaysDict', 'AttrDict', 'DefaultAttrDict', 'moveListItem', 'namedlist', 'classproperty', 'MissingAttrFormatter', 'getitem', 'setitem', 'getitemdef', 'getitemdeep', 'setitemdeep', 'getattrdeep', 'setattrdeep', 'ExplodingMock', 'ScopedSetattr']


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
        except KeyError as e:
            if k.startswith("__"):
                raise AttributeError from e
            return None

    def __setattr__(self, k, v):
        self[k] = v

    def __dir__(self):
        return self.keys()


class DefaultAttrDict(dict):
    'Augment a dict with more convenient .attr syntax.  not-present keys store new DefaultAttrDict.  like a recursive defaultdict.'
    def __getattr__(self, k):
        if k not in self:
            if k.startswith("__"):
                raise AttributeError from e
            self[k] = DefaultAttrDict()
        return self[k]

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


def setitem(r, i, v):  # function needed for use in lambda
    r[i] = v
    return True

def getitem(o, k, default=None):
    return default if o is None else o[k]

def getitemdef(o, k, default=None):
    try:
        return default if o is None else o[k]
    except Exception:
        return default


def getattrdeep(obj, attr, *default, getter=getattr):
    try:
        'Return dotted attr (like "a.b.c") from obj, or default if any of the components are missing.'
        if not isinstance(attr, str):
            return getter(obj, attr, *default)

        try:  # if attribute exists, return toplevel value, even if dotted
            if attr in obj:
                return getter(obj, attr)
        except RecursionError:  #1696
            raise
        except Exception as e:
            pass

        attrs = attr.split('.')
        for a in attrs[:-1]:
            obj = getter(obj, a)

        return getter(obj, attrs[-1])
    except Exception as e:
        if not default: raise
        return default[0]


def setattrdeep(obj, attr, val, getter=getattr, setter=setattr):
    'Set dotted attr (like "a.b.c") on obj to val.'
    if not isinstance(attr, str):
        return setter(obj, attr, val)

    try:  # if attribute exists, overwrite toplevel value, even if dotted
        getter(obj, attr)
        return setter(obj, attr, val)
    except Exception as e:
        pass

    attrs = attr.split('.')
    for a in attrs[:-1]:
        try:
            obj = getter(obj, a)
        except Exception as e:
            obj = obj[a] = type(obj)()  # assume homogeneous nesting

    setter(obj, attrs[-1], val)


def getitemdeep(obj, k, *default):
    if not isinstance(k, str):
        try:
            return obj[k]
        except IndexError:
            pass
    return getattrdeep(obj, k, *default, getter=getitem)

def setitemdeep(obj, k, val):
    return setattrdeep(obj, k, val, getter=getitemdef, setter=setitem)


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
            except ValueError as e:
                raise AttributeError from e

        def __setattr__(self, k, v):
            'to enable .fieldname ='
            try:
                self[self._fields.index(k)] = v
            except ValueError:
                super().__setattr__(k, v)

    return NamedListTemplate


class ExplodingMock:
    'A mock object that raises an exception for everything except conversion to True/False.'
    def __init__(self, msg):
        self.__msg = msg

    def __getattr__(self, k):
        raise Exception(self.__msg)

    def __bool__(self):
        return False


class MissingAttrFormatter(string.Formatter):
    "formats {} fields with `''`, that would normally result in a raised KeyError or AttributeError or IndexError; intended for user customisable format strings."
    def get_value(self, key, args, kwargs):
        try:
            return super().get_value(key, args, kwargs)
        except Exception:
            raise

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, AttributeError, IndexError, ValueError) as e:
            return ('{' + field_name + '}', field_name)

    def format_field(self, value, format_spec):
        # value is missing
        if value is None:
            return ''
        elif not value:
            return str(value)
        return super().format_field(value, format_spec)


@contextmanager
def ScopedSetattr(obj, attrname, val):
    oldval = getattr(obj, attrname)
    try:
        setattr(obj, attrname, val)
        yield
    finally:
        setattr(obj, attrname, oldval)
