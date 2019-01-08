import operator


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
                L = [None]*len(fieldnames)
            super().__init__(L)
            for k, v in kwargs.items():
                setattr(self, k, v)

        @classmethod
        def length(cls):
            return len(cls._fields)

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

    for i, attrname in enumerate(fieldnames):
        # create property getter/setter for each field
        setattr(NamedListTemplate, attrname, property(operator.itemgetter(i), itemsetter(i)))

    return NamedListTemplate
