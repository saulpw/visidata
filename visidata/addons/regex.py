from visidata import *

command(';', 'splitColumnByRegex(columns, cursorColIndex, cursorCol, cursorValue, input("split regex: ", type="regex"))', 'split column by regex')
command('.', 'columns.insert(cursorColIndex+1, regexTransform(cursorCol, input("transform column by regex: ", type="regex")))', 'transform column by regex')

def splitColumnByRegex(columns, colIndex, origcol, exampleVal, regexstr):
    regex = re.compile(regexstr, regex_flags())

    result = regex.search(exampleVal)

    for i, g in enumerate(result.groups()):
        c = Column(origcol.name+'_re'+str(i),
                getter=lambda row, regex=regex, i=i, origcol=origcol: regex.search(origcol.getValue(row)).group(i+1))

        columns.insert(colIndex+i+1, c)

def regexTransform(col, instr):
    i = index_with_escape(instr, '/')
    before = instr[:i]
    after = instr[i+1:]
    newCol = Column(col.name + '_re',
                    getter=lambda row, col=col, before=before, after=after: re.sub(before, after, col.getValue(row), flags=regex_flags()))
    return newCol

def index_with_escape(s, char, escape_char='\\'):
    i=0
    while i < len(s):
        if s[i] == escape_char:
            i += 1
        elif s[i] == char:
            return i
        i += 1

    return None
