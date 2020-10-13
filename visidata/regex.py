import re
import random

from visidata import asyncthread, option, options, vd
from visidata import BaseSheet, Sheet, Column, Progress


@Sheet.api
def setSubst(sheet, cols, rows):
    if not rows:
        vd.warning('no %s selected' % sheet.rowtype)
        return
    modified = 'column' if len(cols) == 1 else 'columns'
    rex = vd.input("transform %s by regex: " % modified, type="regex-subst")
    setValuesFromRegex(cols, rows, rex)


option('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]', replay=True)
option('regex_maxsplit', 0, 'maxsplit to pass to regex.split', replay=True)
option('default_sample_size', 100, 'number of rows to sample for regex.split', replay=True)

def makeRegexSplitter(regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

def makeRegexMatcher(regex, origcol):
    def _regexMatcher(row):
        m = regex.search(origcol.getDisplayValue(row))
        if m:
            return m.groups()
    return _regexMatcher

@asyncthread
def addRegexColumns(regexMaker, vs, origcol, regexstr):
    regexstr or vd.fail('regex required')

    regex = re.compile(regexstr, vs.regex_flags())

    func = regexMaker(regex, origcol)

    n = options.default_sample_size
    if n and n < len(vs.rows):
        exampleRows = random.sample(vs.rows, max(0, n-1))  # -1 to account for included cursorRow
    else:
        exampleRows = vs.rows

    cols = []
    ncols = 0  # number of new columns added already
    for r in Progress(exampleRows + [vs.cursorRow]):
        try:
            m = func(r)
            if not m:
                continue
        except Exception as e:
            vd.exceptionCaught(e)

        for _ in range(len(m)-len(cols)):
            cols.append(Column(origcol.name+'_re'+str(len(cols)),
                            getter=lambda col,row,i=len(cols),func=func: func(row)[i],
                            origCol=origcol))

    vs.addColumnAtCursor(*cols)


def regexTransform(origcol, instr):
    i = indexWithEscape(instr, '/')
    if i is None:
        before = instr
        after = ''
    else:
        before = instr[:i]
        after = instr[i+1:]
    return lambda col,row,origcol=origcol,before=before,after=after,flags=origcol.sheet.regex_flags(): re.sub(before, after, origcol.getDisplayValue(row), flags=flags)

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
    vd.addUndoSetValues(cols, rows)
    for r in Progress(rows, 'replacing'):
        for col, transform in zip(cols, transforms):
            col.setValueSafe(r, transform(col, r))
    for col in cols:
        col.recalc()


@BaseSheet.api
def regex_flags(sheet):
    'Return flags to pass to regex functions from options'
    return sum(getattr(re, f.upper()) for f in options.regex_flags)


Sheet.addCommand(':', 'split-col', 'addRegexColumns(makeRegexSplitter, sheet, cursorCol, input("split regex: ", type="regex-split"))', 'add new columns from regex split; number of columns determined by example row at cursor')
Sheet.addCommand(';', 'capture-col', 'addRegexColumns(makeRegexMatcher, sheet, cursorCol, input("match regex: ", type="regex-capture"))', 'add new column from capture groups of regex; requires example row')
Sheet.addCommand('*', 'addcol-subst', 'addColumnAtCursor(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, input("transform column by regex: ", type="regex-subst"))))', 'add column derived from current column, replacing regex with subst (may include \1 backrefs)')
Sheet.addCommand('g*', 'setcol-subst', 'setSubst([cursorCol], selectedRows)', 'regex/subst - modify selected rows in current column, replacing regex with subst, (may include backreferences \\1 etc)')
Sheet.addCommand('gz*', 'setcol-subst-all', 'setSubst(visibleCols, selectedRows)', 'modify selected rows in all visible columns, replacing regex with subst (may include \\1 backrefs)')
