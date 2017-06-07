command(';', 'splitColumnByRegex(columns, cursorColIndex, cursorCol, cursorValue, input("split regex: "))', 'split column by regex')

def splitColumnByRegex(columns, colIndex, origcol, exampleVal, regexstr):
    regex = re.compile(regexstr)  # TODO: regex_flags

    result = regex.search(exampleVal)

    for i, g in enumerate(result.groups()):
        c = Column(origcol.name+'_'+str(i),
                getter=lambda row, regex=regex, i=i, origcol=origcol: regex.search(origcol.getValue(row)).group(i+1))

        columns.insert(colIndex+i+1, c)
