from visidata import *

Sheet.addCommand(':', 'split-col', 'addRegexColumns(makeRegexSplitter, sheet, cursorColIndex, cursorCol, input("split regex: ", type="regex-split"))', undo=undoAddCols)
Sheet.addCommand(';', 'capture-col', 'addRegexColumns(makeRegexMatcher, sheet, cursorColIndex, cursorCol, input("match regex: ", type="regex-capture"))', undo=undoAddCols)
Sheet.addCommand('*', 'addcol-subst', 'addColumn(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, input("transform column by regex: ", type="regex-subst"))), cursorColIndex+1)', undo=undoAddCols)
Sheet.addCommand('g*', 'setcol-subst', 'rex=input("transform column by regex: ", type="regex-subst"); setValuesFromRegex([cursorCol], selectedRows, rex)', undo=undoEditCells)
Sheet.addCommand('gz*', 'setcol-subst-all', 'rex=input("transform columns by regex: ", type="regex-subst"); setValuesFromRegex(visibleCols, selectedRows, rex)', undo=undoSetValues('selectedRows', 'visibleCols'))

replayableOption('regex_maxsplit', 0, 'maxsplit to pass to regex.split')
replayableOption('default_sample_size', 100, 'number of rows to sample for regex.split')

def makeRegexSplitter(regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

def makeRegexMatcher(regex, origcol):
    return lambda row, regex=regex, origcol=origcol: regex.search(origcol.getDisplayValue(row)).groups()

@asyncthread
def addRegexColumns(regexMaker, vs, colIndex, origcol, regexstr):
    regex = re.compile(regexstr, regex_flags())

    func = regexMaker(regex, origcol)

    n = options.default_sample_size
    if n and n < len(vs.rows):
        exampleRows = random.sample(vs.rows, max(0, n-1))  # -1 to account for included cursorRow
    else:
        exampleRows = vs.rows

    ncols = 0  # number of new columns added already
    for r in Progress(exampleRows + [vs.cursorRow]):
        for _ in range(len(func(r))-ncols):
            c = Column(origcol.name+'_re'+str(ncols),
                            getter=lambda col,row,i=ncols,func=func: func(row)[i],
                            origCol=origcol)
            vs.addColumn(c, index=colIndex+ncols+1)
            ncols += 1


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


@asyncthread
def setValuesFromRegex(cols, rows, rex):
    transforms = [regexTransform(col, rex) for col in cols]
    for r in Progress(rows, 'replacing'):
        for col, transform in zip(cols, transforms):
            col.setValueSafe(r, transform(col, r))
    for col in cols:
        col.recalc()
