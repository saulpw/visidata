command(';', 'splitColumnByRegex(columns, cursorColIndex, cursorCol, cursorValue, input("split regex: "))', 'split column by regex')
command('.', 'columns.insert(cursorColIndex+1, regexTransform(cursorCol, input("transform column by regex: ")))', 'transform column by regex')

def splitColumnByRegex(columns, colIndex, origcol, exampleVal, regexstr):
    regex = re.compile(regexstr)  # TODO: regex_flags

    result = regex.search(exampleVal)

    for i, g in enumerate(result.groups()):
        c = Column(origcol.name+'_'+str(i),
                getter=lambda row, regex=regex, i=i, origcol=origcol: regex.search(origcol.getValue(row)).group(i+1))

        columns.insert(colIndex+i+1, c)

def regexTransform(col, instr):
    before, after = instr.split('/')
    newCol = Column(col.name + '_new',
                    getter=lambda row, col=col, before=before, after=after: re.sub(before, after, col.getValue(row)))
    return newCol
