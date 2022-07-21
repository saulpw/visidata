import functools
from visidata import clipdraw, colors, BaseSheet, VisiData, VisiDataMetaSheet, vd, EscapeException, AttrDict, ENTER


@VisiData.api
def open_mnu(vd, p):
    return FormSheet(p.name, source=p)


vd.save_mnu=vd.save_tsv

class FormSheet(VisiDataMetaSheet):
    rowtype='labels' # rowdef: { .x .y .text .color .command .input .underline}

@VisiData.api
def replayCommand(vd, longname, sheet=None, col='', row=''):
    vd.replayOne(vd.cmdlog.newRow(sheet=self.name, col=col, row=row, longname=r.command, input=r.input))


class FormCanvas(BaseSheet):
    rowtype='labels'
    def click(self, r):
        vd.replayCommand(r.command, sheet=self)

    def reload(self):
        self.rows = self.source.rows

    def draw(self, scr):
        vd.clearCaches()
        h, w = scr.getmaxyx()
        for r in self.source.rows:
            if not r.text:
                continue
            x, y = r.x, r.y
            if isinstance(y, float) and (0 < y < 1) or (-1 < y < 0): y = h*y
            if isinstance(x, float) and (0 < x < 1) or (-1 < x < 0): x = w*x-(len(r.text)/2)
            x = int(x)
            y = int(y)
            if y < 0: y += h
            if x < 0: x += w
            clipdraw(scr, y, x, r.text, colors[r.color])
            # underline first occurrence of r.underline in r.text
            if hasattr(r, 'underline') and r.underline:
                index = r.text.find(r.underline)
                clipdraw(scr, y, x+index, r.text[index:len(r.underline)+1], colors[r.color + " underline"])
            vd.onMouse(scr, y, x, 1, len(r.text), BUTTON1_RELEASED=lambda y,x,key,r=r,sheet=self: sheet.click(r))

    def run(self, scr):
        vd.setWindows(vd.scrFull)
        drawnrows = [r for r in self.source.rows if r.text]
        inputs = [r for r in self.source.rows if r.input]
        maxw = max(int(r.x)+len(r.text) for r in drawnrows)
        maxh = max(int(r.y) for r in drawnrows)
        h, w = vd.scrFull.getmaxyx()
        y, x = max(0, (h-maxh)//2-1), max(0, (w-maxw)//2-1)
        self.scrForm = vd.scrFull.derwin(min(h-1, maxh+2), min(w-1, maxw+1), y, x)
        self.scrForm.keypad(1)
        curinput = inputs[0] if inputs else None
        while True:
            vd.draw_all()

            self.scrForm.erase()
            self.scrForm.border()
            self.draw(self.scrForm)

            k = vd.getkeystroke(self.scrForm, self)
            if k in ['^C', '^Q', '^[', 'q']:
                return {}
            if curinput and k in curinput.keystrokes:
                return {curinput.input: k}


@functools.wraps(VisiData.confirm)
@VisiData.api
def confirm(vd, prompt, exc=EscapeException):
    'Display *prompt* on status line and demand input that starts with "Y" or "y" to proceed.  Raise *exc* otherwise.  Return True.'
    if vd.options.batch:
        return vd.fail('cannot confirm in batch mode: ' + prompt)

    form = FormSheet('confirm', rows=[
        AttrDict(x=2, y=0, text=' confirm ', color='yellow'),
        AttrDict(x=2, y=1, text=prompt, color='yellow'),
        AttrDict(x=.25, y=2, text=' yes ', color='black on yellow bold', underline='y'),
        AttrDict(x=.75, y=2, text=' no ', color='black on yellow bold', underline='n'),
        AttrDict(input='yn', keystrokes=['y', 'n', ENTER]),
    ])

    ret = FormCanvas(source=form).run(vd.scrFull)
    if not ret:
        raise exc('')
    yn = ret['yn'][:1]
    if not yn or yn not in 'Yy':
        msg = 'disconfirmed: ' + prompt
        if exc:
            raise exc(msg)
        vd.warning(msg)
        return False
    return True
