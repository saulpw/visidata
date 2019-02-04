'Various helper classes and functions.'

class AttrDict(dict):
    'Augment a dict with more convenient .attr syntax.'
    def __getattr__(self, k):
        return self[k]

    def __setattr__(self, k, v):
        self[k] = v
