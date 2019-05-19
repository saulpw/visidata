from functools import wraps


__all__ = ['Extensible']

class Extensible:
    @classmethod
    def init(cls, membername, initfunc, **kwargs):
        'Add `self.attr=T()` to cls.__init__.  Usage: cls.init("attr", T[, copy=True])'
        oldinit = cls.__init__
        def newinit(self, *args, **kwargs):
            oldinit(self, *args, **kwargs)
            setattr(self, membername, initfunc())
        cls.__init__ = newinit

        oldcopy = cls.__copy__
        def newcopy(self, *args, **kwargs):
            ret = oldcopy(self, *args, **kwargs)
            setattr(ret, membername, getattr(self, membername) if kwargs.get('copy', False) else initfunc())
            return ret
        cls.__copy__ = newcopy

    @classmethod
    def api(cls, func):
        oldfunc = getattr(cls, func.__name__, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, func.__name__, func)
        return func

    @classmethod
    def class_api(cls, func):
        name = func.__get__(None, dict).__func__.__name__
        oldfunc = getattr(cls, name, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, name, func)
        return func

    @classmethod
    def property(cls, func):
        @property
        def dofunc(self):
            return func(self)
        setattr(cls, func.__name__, dofunc)
        return dofunc

    @classmethod
    def cached_property(cls, func):
        @property
        @wraps(func)
        def get_if_not(self):
            name = '_' + func.__name__
            if not hasattr(self, name):
                setattr(self, name, func(self))
            return getattr(self, name)
        setattr(cls, func.__name__, get_if_not)
        return get_if_not
