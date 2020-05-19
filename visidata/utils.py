import operator

'Various helper classes and functions.'

__all__ = ['AttrDict', 'moveListItem', 'namedlist', 'classproperty']


class AttrDict(dict):
    'Augment a dict with more convenient .attr syntax.  not-present keys return None.'
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
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
