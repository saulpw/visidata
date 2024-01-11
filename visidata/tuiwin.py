from visidata import VisiData, vd, BaseSheet

vd._parentscrs = {}  # scr -> parentscr


@VisiData.api
def subwindow(vd, scr, x, y, w, h):
    'Return subwindow with its (0,0) at (x,y) relative to parent scr.  Replacement for scr.derwin() to track parent scr.'
    newscr = scr.derwin(h, w, y, x)
    vd._parentscrs[newscr] = scr
    return newscr


@VisiData.api
def getrootxy(vd, scr):  # like scr.getparyx() but for all ancestor scrs
    px, py = 0, 0
    while scr in vd._parentscrs:
        dy, dx = scr.getparyx()
        if dy > 0: py += dy
        if dx > 0: px += dx
        scr = vd._parentscrs[scr]
    return px, py


vd.bindkey('Alt+[Shift+I', 'no-op')  #2247 focus-in
vd.bindkey('Alt+[Shift+O', 'no-op')  # focus-out
