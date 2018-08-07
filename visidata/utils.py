
def joinSheetnames(*sheetnames):
    'Concatenate sheet names in a standard way'
    return '_'.join(str(x) for x in sheetnames)


def moveListItem(L, fromidx, toidx):
    "Move element within list `L` and return element's new index."
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
            exceptionCaught(e)
