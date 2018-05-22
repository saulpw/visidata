
def joinSheetnames(*sheetnames):
    'Concatenate sheet names in a standard way'
    return '_'.join(str(x) for x in sheetnames)


def moveListItem(L, fromidx, toidx):
    "Move element within list `L` and return element's new index."
    r = L.pop(fromidx)
    L.insert(toidx, r)
    return toidx
