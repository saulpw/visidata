import re
import random

from visidata import asyncthread, options, vd
from visidata import VisiData, BaseSheet, Sheet, Column, Progress


@VisiData.lazy_property
def help_regex(vd):
    return vd.getHelpPane('regex', module='visidata')


vd.option('regex_maxsplit', 0, 'maxsplit to pass to regex.split', replay=True)

@VisiData.api
def makeRegexSplitter(vd, regex, origcol):
    return lambda row, regex=regex, origcol=origcol, maxsplit=options.regex_maxsplit: regex.split(origcol.getDisplayValue(row), maxsplit=maxsplit)

@VisiData.api
def makeRegexMatcher(vd, regex, origcol):
    if not regex.groups:
        vd.fail('specify a capture group')  #1778
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
        m = vd.callNoExceptions(func, r)
        if not m:
            continue

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

    if not cols:
        vd.warning("no regex matches found, didn't add column")
        return

    vs.addColumnAtCursor(*cols.values())


@VisiData.api
def regexTransform(vd, origcol, before='', after=''):
    return lambda col,row,origcol=origcol,before=before,after=after,flags=origcol.sheet.regex_flags(): re.sub(before, after, origcol.getDisplayValue(row), flags=flags)


@VisiData.api
def parse_sed_transform(vd, instr):
    i = indexWithEscape(instr, '/')
    if i is None:
        return instr, ''
    else:
        return instr[:i], instr[i+1:]


def indexWithEscape(s, char, escape_char='\\'):
    i=0
    while i < len(s):
        if s[i] == escape_char:
            i += 1
        elif s[i] == char:
            return i
        i += 1

    return None


@Sheet.api
@asyncthread
def setValuesFromRegex(sheet, cols, rows, before='', after=''):
    transforms = [vd.regexTransform(col, before=before, after=after) for col in cols]
    vd.addUndoSetValues(cols, rows)
    for r in Progress(rows, 'replacing'):
        for col, transform in zip(cols, transforms):
            vd.callNoExceptions(col.setValue, r, transform(col, r))

    for col in cols:
        col.recalc()


@VisiData.api
def inputRegex(vd, prompt, type='regex', **kwargs):
    return vd.input(prompt, type=type, help=vd.help_regex, **kwargs)



@VisiData.api
def inputRegexSubst(vd, prompt):
    'Input regex transform via oneliner (separated with `/`).  Return parsed transformer as dict(before=, after=).'
    return vd.inputMultiple(before=dict(type='regex', prompt='search: ', help=prompt),
                            after=dict(type='regex-replace', prompt='replace: ', help=prompt))


Sheet.addCommand(':', 'addcol-split', 'addColumnAtCursor(RegexColumn(makeRegexSplitter, cursorCol, inputRegex("split regex: ", type="regex-split")))', 'add column split by regex')
Sheet.addCommand(';', 'addcol-capture', 'addColumnAtCursor(RegexColumn(makeRegexMatcher, cursorCol, inputRegex("capture regex: ", type="regex-capture")))', 'add column captured by regex')

Sheet.addCommand('*', 'addcol-regex-subst', 'addColumnAtCursor(Column(cursorCol.name + "_re", getter=regexTransform(cursorCol, **inputRegexSubst("regex transform column"))))', 'add column derived from current column, replacing `search` regex with `replace` (may include \\1 backrefs)')
Sheet.addCommand('g*', 'setcol-regex-subst', 'setValuesFromRegex([cursorCol], someSelectedRows, **inputRegexSubst("regex transform column"))', 'modify selected rows in current column, replacing `search` regex with `replace`, (may include backreferences \\1 etc)')
Sheet.addCommand('gz*', 'setcol-regex-subst-all', 'setValuesFromRegex(visibleCols, someSelectedRows, **inputRegexSubst(f"regex transform {nVisibleCols} columns"))', 'modify selected rows in all visible columns, replacing `search` regex with `replace` (may include \\1 backrefs)')


vd.addMenuItems('''
    Edit > Modify > selected cells > regex substitution > setcol-regex-subst
    Column > Add column > capture by regex > addcol-capture
    Column > Add column > split by regex > addcol-split
    Column > Add column > subst by regex > addcol-regex-subst
    Row > Select > by regex > current column > select-col-regex
    Row > Select > by regex > all columns > select-cols-regex
    Row > Unselect > by regex > current column > unselect-col-regex
    Row > Unselect > by regex > all columns > unselect-cols-regex
''')
