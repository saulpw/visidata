from visidata import *

Sheet.addCommand(':', 'split-col', 'addRegexColumns(makeRegexSplitter, sheet, cursorColIndex, cursorCol, cursorRow, input("split regex: ", type="regex-split"))')
Sheet.addCommand(';', 'capture-col', 'addRegexColumns(makeRegexMatcher, sheet, cursorColIndex, cursorCol, cursorRow, input("match regex: ", type="regex-capture"))')
Sheet.addCommand('*', 'addcol-subst', 'addColumn(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, input("transform column by regex: ", type="regex-subst"))), cursorColIndex+1)')
Sheet.addCommand('g*', 'setcol-subst', 'rex=input("transform column by regex: ", type="regex-subst"); setValuesFromRegex(cursorCol, selectedRows or rows, rex)')

replayableOption('regex_maxsplit', 0, 'maxsplit to pass to regex.split')

def makeRegexSplitter(regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

def makeRegexMatcher(regex, origcol):
    return lambda row, regex=regex, origcol=origcol: regex.search(origcol.getDisplayValue(row)).groups()

def addRegexColumns(regexMaker, vs, colIndex, origcol, exampleRow, regexstr):
    regex = re.compile(regexstr, regex_flags())

    func = regexMaker(regex, origcol)
    result = func(exampleRow)

    for i, g in enumerate(result):
        c = Column(origcol.name+'_re'+str(i), getter=lambda col,row,i=i,func=func: func(row)[i])
        c.origCol = origcol
        vs.addColumn(c, index=colIndex+i+1)


def regexTransform(origcol, instr):
    i = indexWithEscape(instr, '/')
    if i is None:
        before = instr
        after = ''
    else:
        before = instr[:i]
        after = instr[i+1:]
    return lambda col,row,origcol=origcol,before=before, after=after: re.sub(before, after, origcol.getDisplayValue(row), flags=regex_flags())

def indexWithEscape(s, char, escape_char='\\'):
    i=0
    while i < len(s):
        if s[i] == escape_char:
            i += 1
        elif s[i] == char:
            return i
        i += 1

    return None


def setValuesFromRegex(col, rows, rex):
    transform = regexTransform(col, rex)
    for r in rows:
        col.setValue(r, transform(col, r))
    col.recalc()
