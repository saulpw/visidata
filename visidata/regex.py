from visidata import *

globalCommand(':', 'addRegexColumns(makeRegexSplitter, sheet, cursorColIndex, cursorCol, cursorRow, input("split regex: ", type="regex"))', 'add new columns from regex split; # columns determined by example row at cursor')
globalCommand(';', 'addRegexColumns(makeRegexMatcher, sheet, cursorColIndex, cursorCol, cursorRow, input("match regex: ", type="regex"))', 'add new column from capture groups of regex; also requires example row')
globalCommand('*', 'addColumn(regexTransform(cursorCol, input("transform column by regex: ", type="regex")), cursorColIndex+1)', 'regex/subst - replace regex with subst, which may include backreferences (\\1 etc)')

option('regex_maxsplit', 0, 'maxsplit to pass to regex.split')

def makeRegexSplitter(regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

def makeRegexMatcher(regex, origcol):
    return lambda row, regex=regex, origcol=origcol: regex.search(origcol.getDisplayValue(row)).groups()

def addRegexColumns(regexMaker, vs, colIndex, origcol, exampleRow, regexstr):
    regex = re.compile(regexstr, regex_flags())

    func = regexMaker(regex, origcol)
    result = func(exampleRow)

    for i, g in enumerate(result):
        c = Column(origcol.name+'_re'+str(i), getter=lambda r,i=i,func=func: func(r)[i])
        vs.addColumn(c, index=colIndex+i+1)


def regexTransform(col, instr):
    i = indexWithEscape(instr, '/')
    if i is None:
        before = instr
        after = ''
    else:
        before = instr[:i]
        after = instr[i+1:]
    newCol = Column(col.name + '_re',
                    getter=lambda row, col=col, before=before, after=after: re.sub(before, after, col.getDisplayValue(row), flags=regex_flags()))
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
