import re
from visidata import vd, VisiData, Sheet


vd.option('clean_names', False, 'clean column/sheet names to be valid Python identifiers', replay=True)


@VisiData.global_api
def cleanName(vd, s):
    #[Nas Banov] https://stackoverflow.com/a/3305731
    #    return re.sub(r'\W|^(?=\d)', '_', str(s)).strip('_')
    s = re.sub(r'[^\w\d_]', '_', s)  # replace non-alphanum chars with _
    s = re.sub(r'_+', '_', s)  # replace runs of _ with a single _
    s = s.strip('_')
    return s


@Sheet.api
def maybeClean(sheet, s):
    if sheet.options.clean_names:
        s = vd.cleanName(s)
    return s


Sheet.addCommand('', 'clean-names', '''
options.clean_names = True;
for c in visibleCols:
    c.name = cleanName(c.name)
''', 'set options.clean_names on sheet and clean visible column names')
