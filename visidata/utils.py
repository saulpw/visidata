
def joinSheetnames(*sheetnames):
    'Concatenate sheet names in a standard way'
    return '_'.join(str(x) for x in sheetnames)
