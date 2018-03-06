from visidata import *


class StatusMaker:
    def __init__(self, name, *args, **kwargs):
        self._name = name

    def __getattr__(self, k):
        return StatusMaker(status('%s.%s' % (self._name, k)))

#    def __setattr__(self, k, v):
#        super().__setattr__(k, v)
#        if k != '_name':
#            status('%s.%s := %s' % (self._name, k, v))

    def __call__(self, *args, **kwargs):
        return StatusMaker(status('%s(%s, %s)' % (self._name, ', '.join(str(x) for x in args), kwargs)))
