from visidata import *

command(':', 'addRegexColumns(makeRegexSplitter, columns, cursorColIndex, cursorCol, cursorRow, input("split regex: ", type="regex"))', 'add columns by regex split')
command(';', 'addRegexColumns(makeRegexMatcher, columns, cursorColIndex, cursorCol, cursorRow, input("match regex: ", type="regex"))', 'add columns by regex match')
command('*', 'columns.insert(cursorColIndex+1, regexTransform(cursorCol, input("transform column by regex: ", type="regex")))', 'transform column by regex')

option('regex_maxsplit', 0, 'maxsplit to pass to regex.split')

def makeRegexSplitter(regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getValue(row), maxsplit=0)

def makeRegexMatcher(regex, origcol):
    return lambda row, regex=regex, origcol=origcol: regex.search(origcol.getValue(row)).groups()

def addRegexColumns(regexMaker, columns, colIndex, origcol, exampleRow, regexstr):
    regex = re.compile(regexstr, regex_flags())

    func = regexMaker(regex, origcol)
    result = func(exampleRow)

    for i, g in enumerate(result):
        columns.insert(colIndex+i+1, Column(origcol.name+'_re'+str(i), getter=lambda r,i=i,func=func: func(r)[i]))


def regexTransform(col, instr):
    i = indexWithEscape(instr, '/')
    if i is None:
        before = instr
        after = ''
    else:
        before = instr[:i]
        after = instr[i+1:]
    newCol = Column(col.name + '_re',
                    getter=lambda row, col=col, before=before, after=after: re.sub(before, after, col.getValue(row), flags=regex_flags()))
    return newCol

def indexWithEscape(s, char, escape_char='\\'):
    i=0
    while i < len(s):
        if s[i] == escape_char:
            i += 1
        elif s[i] == char:
            return i
        i += 1

    return None
