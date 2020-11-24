from visidata import *

def open_mnu(p):
    return MenuSheet(p.name, source=p)


vd.save_mnu=vd.save_tsv

class MenuSheet(VisiDataMetaSheet):
    rowtype='labels' # { .x .y .text .color .command .input }


class MenuCanvas(BaseSheet):
    rowtype='labels'
    def click(self, r):
        vd.replayOne(vd.cmdlog.newRow(sheet=self.name, col='', row='', longname=r.command, input=r.input))

    def reload(self):
        self.rows = self.source.rows

    def draw(self, scr):
        vd.clearCaches()
        for r in Progress(self.source.rows):
            x, y = map(int, (r.x, r.y))
            clipdraw(scr, y, x, r.text, colors[r.color])
            vd.onMouse(scr, y, x, 1, len(r.text), BUTTON1_RELEASED=lambda y,x,key,r=r,sheet=self: sheet.click(r))


MenuSheet.addCommand('z.', 'disp-menu', 'vd.push(MenuCanvas(name, "disp", source=sheet))', '')
