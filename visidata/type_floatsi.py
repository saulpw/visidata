from visidata import VisiData, vd, Sheet

vd.si_prefixes='p n u m . kK M G T P Q'.split()


@VisiData.api
def SIFormatter(vd, fmtstr, val):
    level = 4
    if val != 0:
        while abs(val) > 1000:
            val /= 1000
            level += 1
        while abs(val) < 0.001:
            val *= 1000
            level -= 1

    return vd.numericFormatter(fmtstr, val) + (vd.si_prefixes[level][0] if level != 4 else '')


@vd.numericType('‱', formatter=vd.SIFormatter)
def floatsi(*args):
    if not args:
        return 0.0
    if not isinstance(args[0], str):
        return float(args[0])

    s=args[0].strip()
    for i, p in enumerate(vd.si_prefixes):
        if s[-1] in p:
            return float(s[:-1]) * (1000 ** (i-4))

    return float(s)


Sheet.addCommand('z%', 'type-floatsi', 'cursorCol.type = floatsi', 'set type of current column to SI float')

vd.addMenuItems('''
    Column > Type as > SI float > type-floatsi
''')
