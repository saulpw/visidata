'''History palette: shows previous inputs during search/regex/etc input.'''

from visidata import vd, VisiData, clipdraw, colors


class HistoryPalette:
    'Manages state, navigation, and drawing for the history input palette.'
    def __init__(self, sheet, items, input_height, updater):
        'Initialize palette state from history items.'
        self.sheet = sheet
        self.items = items                                    # raw history list
        self.haystack = [dict(input=item) for item in items]  # precomputed for fuzzymatch
        self.display = [(item, item) for item in items]       # (formatted_text, raw_value)
        self.cursor = -1       # -1 = free-typing, 0+ = index into display
        self.top = 0           # first visible row
        self.orig = ''         # saved input before history navigation
        self.input_height = input_height
        self.updater = updater # caller's original updater to chain

    def nvis(self):
        'Max visible rows for the palette given current window size.'
        return max(1, min(self.sheet.windowHeight - 2 - self.input_height, vd.options.disp_cmdpal_max))

    def bounds(self):
        'Clamp cursor and top, then enforce cursor visibility.'
        n = len(self.display)
        if n == 0: return
        nv = self.nvis()
        self.cursor = max(0, min(self.cursor, n - 1))
        self.top = max(0, min(self.top, n - 1))
        if self.top > self.cursor:              self.top = self.cursor
        if self.top + nv - 1 < self.cursor:     self.top = self.cursor - nv + 1

    def enter_nav(self, v):
        'Save orig and place cursor at end of display list.'
        self.orig = v
        self.cursor = len(self.display) - 1
        self.top = max(0, self.cursor - self.nvis() + 1)

    def sel(self):
        'Return (value, cursor_pos) for current cursor selection.'
        v = self.display[self.cursor][1]
        return v, len(v)

    def nav_up(self, v, i):
        'Move cursor up one item, entering nav mode if needed.'
        if not self.display: return v, i
        if self.cursor == -1:
            self.enter_nav(v)
        else:
            self.cursor -= 1
            self.bounds()
        return self.sel()

    def nav_down(self, v, i):
        'Move cursor down one item, or restore original text at bottom.'
        if not self.display or self.cursor == -1: return v, i
        if self.cursor >= len(self.display) - 1:
            self.cursor = -1  # restore original typed text
            v = self.orig
            return v, len(v)
        self.cursor += 1
        self.bounds()
        return self.sel()

    def nav_pgup(self, v, i):
        'Scroll up one page.'
        if not self.display: return v, i
        if self.cursor == -1: self.enter_nav(v)
        nv = self.nvis()
        old_top = self.top
        self.cursor -= nv - 1
        self.top = old_top - nv + 1      # bottom = old top
        self.bounds()
        return self.sel()

    def nav_pgdn(self, v, i):
        'Scroll down one page.'
        if not self.display or self.cursor == -1: return v, i
        nv = self.nvis()
        old_bottom = self.top + nv - 1
        self.cursor += nv - 1
        self.top = old_bottom             # top = old bottom
        self.bounds()
        return self.sel()

    def nav_home(self, v, i):
        'Jump to first item, or move text cursor to start if not navigating.'
        if self.cursor == -1: return v, 0  # text cursor to start of line
        self.cursor = 0
        self.top = 0
        return self.sel()

    def nav_end(self, v, i):
        'Jump to last item, or move text cursor to end if not navigating.'
        if self.cursor == -1: return v, len(v)  # text cursor to end of line
        self.cursor = len(self.display) - 1
        self.bounds()
        return self.sel()

    def draw(self, value):
        'Update display list from fuzzy match and draw visible palette rows.'
        self.updater(value)
        scr = self.sheet._scr
        if not scr: return
        nv = self.nvis()
        w = min(100, self.sheet.windowWidth)

        if self.cursor >= 0 and value != self.display[self.cursor][1]:
            self.cursor = -1  # user typed something

        if self.cursor == -1:
            # Recompute display list (nav bindings read this on next keypress)
            if value:
                matches = vd.fuzzymatch(self.haystack, value.split())
                self.display = [(m.formatted.get('input', m.match['input']), m.match['input']) for m in matches]
            else:
                self.display = [(item, item) for item in self.items]
            return  # don't draw until user navigates

        if not self.display: return
        ndisplay = min(len(self.display), nv)
        vis_start = max(0, min(self.top, len(self.display) - ndisplay))
        self.top = vis_start
        highlight = self.cursor - vis_start

        visible = self.display[vis_start:vis_start + ndisplay]
        if not visible: return
        box_y = self.sheet.windowHeight - ndisplay - self.input_height - 1
        if box_y < 0: return
        pal_cattr = colors.get_color('color_cmdpalette')
        vd.drawBox(scr, 0, box_y, w, ndisplay + 1, pal_cattr, bottom=False)
        for idx, (text, raw) in enumerate(visible):
            if idx == highlight:
                clipdraw(scr, box_y + 1 + idx, 1, f'> {text}', colors.color_menu_spec, w=w - 2)
            else:
                clipdraw(scr, box_y + 1 + idx, 1, f'  {text}', colors.color_cmdpalette, w=w - 2)


@VisiData.around
def input(vd, orig_input, *args, **kwargs):
    'Wrap vd.input() to show history palette when input has previous history.'
    _input_rows = kwargs.pop('_input_rows', 0) or 0
    _history_palette = kwargs.pop('_history_palette', True)
    type = kwargs.get('type')
    history = kwargs.get('history', [])
    updater = kwargs.get('updater', lambda v: None)
    bindings = kwargs.get('bindings', {})

    if not history and type:
        history = list(vd.inputHistory.setdefault(type, {}).keys())
        kwargs['history'] = history

    if not _history_palette \
            or not type \
            or not history \
            or not vd.cursesEnabled \
            or not vd.wantsHelp('cmdpalette'):
        return orig_input(vd, *args, **kwargs)

    sheet = vd.activeSheet
    items = list(history)   # 0=oldest .. N-1=newest
    pal = HistoryPalette(sheet, items, max(_input_rows, 1), updater)

    pal_bindings = dict(bindings)
    pal_bindings['Up'] = pal.nav_up
    pal_bindings['Down'] = pal.nav_down
    pal_bindings['PgUp'] = pal.nav_pgup
    pal_bindings['PgDn'] = pal.nav_pgdn
    pal_bindings['Home'] = pal.nav_home
    pal_bindings['End'] = pal.nav_end

    kwargs['updater'] = pal.draw
    kwargs['bindings'] = pal_bindings
    return orig_input(vd, *args, **kwargs)
