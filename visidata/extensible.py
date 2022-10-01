from functools import wraps, lru_cache


__all__ = ['Extensible', 'cache', 'drawcache', 'drawcache_property']

class Extensible:
    _cache_clearers = []  # list of func() to call in clearCaches()

    @classmethod
    def init(cls, membername, initfunc=lambda: None, copy=False):
        'Append equivalent of ``self.<membername> = initfunc()`` to ``<cls>.__init__``.  If *copy* is True, <membername> will be copied when object is copied.'

        def thisclass_hasattr(cls, k):
            return getattr(cls, k, None) is not getattr(cls.__bases__[0], k, None)

        # must check hasattr first or else this might be parent's __init__
        oldinit = thisclass_hasattr(cls, '__init__') and getattr(cls, '__init__')
        def newinit(self, *args, **kwargs):
            if oldinit:
                oldinit(self, *args, **kwargs)
            else:
                super(cls, self).__init__(*args, **kwargs)
            if not hasattr(self, membername):  # can be overridden by a subclass
                setattr(self, membername, initfunc())
        cls.__init__ = wraps(oldinit)(newinit) if oldinit else newinit

        oldcopy = thisclass_hasattr(cls, '__copy__') and getattr(cls, '__copy__')
        def newcopy(self, *args, **kwargs):
            if oldcopy:
                ret = oldcopy(self, *args, **kwargs)
            else:
                ret = super(cls, self).__copy__(*args, **kwargs)
            setattr(ret, membername, getattr(self, membername) if copy and hasattr(self, membername) else initfunc())
            return ret
        cls.__copy__ = wraps(oldcopy)(newcopy) if oldcopy else newcopy

    @classmethod
    def api(cls, func):
        oldfunc = getattr(cls, func.__name__, None)
        if oldfunc:
            func = wraps(oldfunc)(func)
        setattr(cls, func.__name__, func)
        return func

    @classmethod
    def before(cls, beforefunc):
        funcname = beforefunc.__name__
        oldfunc = getattr(cls, funcname, None)
        if not oldfunc:
            setattr(cls, funcname, beforefunc)

        @wraps(oldfunc)
        def wrappedfunc(*args, **kwargs):
            beforefunc(*args, **kwargs)
            return oldfunc(*args, **kwargs)

        setattr(cls,  funcname, wrappedfunc)
        return wrappedfunc

    @classmethod
    def after(cls, afterfunc):
        funcname = afterfunc.__name__
        oldfunc = getattr(cls, funcname, None)
        if not oldfunc:
            setattr(cls, funcname, afterfunc)

        @wraps(oldfunc)
        def wrappedfunc(*args, **kwargs):
            r = oldfunc(*args, **kwargs)
            afterfunc(*args, **kwargs)
            return r

        setattr(cls,  funcname, wrappedfunc)
        return wrappedfunc

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
        @wraps(func)
        def dofunc(self):
            return func(self)
        setattr(cls, func.__name__, dofunc)
        return dofunc

    @classmethod
    def lazy_property(cls, func):
        'Return ``func()`` on first access and cache result; return cached result thereafter.'
        @property
        @wraps(func)
        def get_if_not(self):
            name = '_' + func.__name__
            if not hasattr(self, name):
                setattr(self, name, func(self))
            return getattr(self, name)
        setattr(cls, func.__name__, get_if_not)
        return get_if_not

    @classmethod
    def cached_property(cls, func):
        'Return ``func()`` on first access, and cache result; return cached result until ``clearCaches()``.'
        @property
        @wraps(func)
        @lru_cache(maxsize=None)
        def get_if_not(self):
            return func(self)
        setattr(cls, func.__name__, get_if_not)
        Extensible._cache_clearers.append(get_if_not.fget.cache_clear)
        return get_if_not

    @classmethod
    def clear_all_caches(cls):
        for func in Extensible._cache_clearers:
            func()


def cache(func):
    'Return func(...) on first access, and cache result; return cached result until clearCaches().'
    @wraps(func)
    @lru_cache(maxsize=None)
    def call_if_not(self, *args, **kwargs):
        return func(self, *args, **kwargs)
    Extensible._cache_clearers.append(call_if_not.cache_clear)
    return call_if_not


# @drawcache is vd alias for @cache, since vd clears it every frame
drawcache = cache

def drawcache_property(func):
    return property(drawcache(func))
