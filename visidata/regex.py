import re
import random

from visidata import asyncthread, options, vd
from visidata import VisiData, BaseSheet, Sheet, Column, Progress


@Sheet.api
def setSubst(sheet, cols, rows):
    if not rows:
        vd.warning('no %s selected' % sheet.rowtype)
        return
    modified = 'column' if len(cols) == 1 else 'columns'
    rex = vd.input("transform %s by regex: " % modified, type="regex-subst")
    setValuesFromRegex(cols, rows, rex)


vd.option('regex_flags', 'I', 'flags to pass to re.compile() [AILMSUX]', replay=True)
vd.option('regex_maxsplit', 0, 'maxsplit to pass to regex.split', replay=True)

@VisiData.api
def makeRegexSplitter(vd, regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

@VisiData.api
def makeRegexMatcher(vd, regex, origcol):
    def _regexMatcher(row):
        m = regex.search(origcol.getDisplayValue(row))
        if m:
            return m.groupdict() if m.groupdict() else m.groups()
    return _regexMatcher


@Sheet.api
def RegexColumn(vs, regexMaker, origcol, regexstr):
    regex = re.compile(regexstr, vs.regex_flags())
    func = regexMaker(regex, origcol)
    return Column(origcol.name+'_re',
                  getter=lambda col,row,func=func: func(row),
                  origCol=origcol)


@Sheet.api
@asyncthread
def addRegexColumns(vs, regexMaker, origcol, regexstr):
    regexstr or vd.fail('regex required')

    regex = re.compile(regexstr, vs.regex_flags())

    func = regexMaker(regex, origcol)

    cols = {}
    ncols = 0  # number of new columns added already
    for r in Progress(vs.getSampleRows()):
        try:
            m = func(r)
            if not m:
                continue
        except Exception as e:
            vd.exceptionCaught(e)

        if isinstance(m, dict):
            for name in m:
                if name in cols:
                    continue
                cols[name] = Column(origcol.name+'_'+str(name),
                                    getter=lambda col,row,name=name,func=func: func(row)[name],
                                    origCol=origcol)
        elif isinstance(m, (tuple, list)):
            for _ in range(len(m)-len(cols)):
                cols[len(cols)] = Column(origcol.name+'_re'+str(len(cols)),
                                         getter=lambda col,row,i=len(cols),func=func: func(row)[i],
                                         origCol=origcol)
        else:
            raise TypeError("addRegexColumns() expects a dict, list, or tuple from regexMaker, but got a "+type(m).__name__)

    vs.addColumnAtCursor(*cols.values())


@VisiData.api
def regexTransform(vd, origcol, instr):
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
    transforms = [vd.regexTransform(col, rex) for col in cols]
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


Sheet.addCommand(':', 'split-col', 'addRegexColumns(makeRegexSplitter, cursorCol, input("split regex: ", type="regex-split"))', 'Add new columns from regex split')
Sheet.addCommand(';', 'capture-col', 'addRegexColumns(makeRegexMatcher, cursorCol, input("capture regex: ", type="regex-capture"))', 'add new column from capture groups of regex; requires example row')
Sheet.addCommand('', 'addcol-split', 'addColumnAtCursor(RegexColumn(makeRegexSplitter, cursorCol, input("split regex: ", type="regex-split")))', 'Add column split by regex')
Sheet.addCommand('', 'addcol-capture', 'addColumnAtCursor(RegexColumn(makeRegexMatcher, cursorCol, input("capture regex: ", type="regex-capture")))', 'Add column captured by regex')
Sheet.addCommand('*', 'addcol-subst', 'addColumnAtCursor(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, input("transform column by regex: ", type="regex-subst"))))', 'add column derived from current column, replacing regex with subst (may include \1 backrefs)')
Sheet.addCommand('g*', 'setcol-subst', 'setSubst([cursorCol], someSelectedRows)', 'regex/subst - modify selected rows in current column, replacing regex with subst, (may include backreferences \\1 etc)')
Sheet.addCommand('gz*', 'setcol-subst-all', 'setSubst(visibleCols, someSelectedRows)', 'modify selected rows in all visible columns, replacing regex with subst (may include \\1 backrefs)')
