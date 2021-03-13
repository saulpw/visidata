from itertools import zip_longest

from visidata import VisiData, AttrDict, dispwidth
from .drawing import Drawing, DrawingSheet

@VisiData.api
def open_scr(vd, p):
    palette = {}  # colorcode -> colorstr
    pcolors = []
    lines = []
    with p.open_text() as fp:
        for line in fp.readlines():
            line = line[:-1]
            if not line: continue
            if line.startswith('#C '):  #C S fg on bg underline reverse
                palette[line[3]] = line[4:].strip()
            elif line.startswith('#M '):  #M mask of color id (S above) corresponding to line
                pcolors.append(line[3:])
            else:
                lines.append(list(line))

    rows=[]
    for y, (line, mask) in enumerate(zip_longest(lines, pcolors)):
        if mask is None: mask = []
        x = 0
        for ch, mch in zip_longest(line, mask):
            if ch == ' ':
                x += 1
            else:
                rows.append(AttrDict(x=x, y=y, text=ch, color=palette[mch] if mch else ''))
                x += dispwidth(ch)

    sheet = DrawingSheet(p.name, 'table', source=p, rows=rows)
    return Drawing(p.name, source=sheet)

