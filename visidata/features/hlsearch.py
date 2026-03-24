from visidata import Sheet, TableSheet, Column
from visidata import vd, dispwidth
import re


# NOTE: both Sheet and Column have highlight_regex, but g/ sets per-column
# (not sheet-level), so sheet.highlight_regex is only used by highlight-sheet.
# clear_search() always wipes both before any new pattern is set, so the
# `col.highlight_regex or sheet.highlight_regex` in drawRow() never chooses
# between two live patterns. The two-attribute model seems like it could be simplified to
# one.  See PR #2861 for discussion.
TableSheet.init('highlight_regex', lambda: None, copy=False)
Column.init('highlight_regex', lambda: None, copy=False)

@Sheet.api
def highlight_chunks(sheet, chunks, hp, hoffset, colwidth, notewidth, cattr, hl_attr):
    '''Highlights *hp* which is a regex to highlight, or None if no highlighting.
       Always handles formatting for *hoffset* even when *hp* is None.
       Consumes the generator *chunks*. Returns a list of (attr, string) pairs.
    '''
    display_chunks = []
    left_hl = False
    right_hl = False
    truncate_right = False  #becomes True only if the highlighted chunk ends at the col edge
    dispw = 0
    for attr, text in chunks:
        last = hoffset if hoffset > 0 else 0
        # note a limitation with Unicode:  the regex can cut a grapheme cluster into codepoints
        matches = re.finditer(hp, text) if hp else []
        for m in matches:
            m1 = m.start()
            m2 = m.end()
            if m1 < hoffset:
                left_hl = True
                if m2 <= hoffset:
                    continue
                m1 = hoffset
            if m1 > last:
                s = text[last:m1]
                if truncate_right:
                    display_chunks[-1][1] += s
                else:
                    display_chunks.append([attr, s])
                dispw += dispwidth(s, literal=True)
            s = text[m1:m2]
            if truncate_right:
                display_chunks[-1][1] += s
            else:
                display_chunks.append([hl_attr, s])
            dispw += dispwidth(text[m1:m2], literal=True)
            if dispw > colwidth-notewidth-1:
                right_hl = True
                last = len(text)
                break
            if dispw == colwidth-notewidth-1:
                #append any subsequent cell text to the highlighted chunk so it gets a truncator added by clipdraw()
                truncate_right = True
            last = m2
        if last < len(text):
            s = text[last:]
            if truncate_right:
                display_chunks[-1][1] += s
            else:
                display_chunks.append([attr, s])
            dispw += dispwidth(s, literal=True)
    return display_chunks, left_hl, right_hl

@Sheet.api
def setHighlightRegex(sheet, r, cols=[]):
    if not sheet.options.highlight_search:
        return
    flagbits = sum(getattr(re, f.upper()) for f in r['flags'])
    rc = re.compile(r['regex'], flagbits)
    sheet.clear_search()
    if cols is None:
        vd.addUndo(setattr, sheet, 'highlight_regex', sheet.highlight_regex)
        sheet.highlight_regex = rc
    else:
        for col in cols:
            vd.addUndo(setattr, col, 'highlight_regex', col.highlight_regex)
            col.highlight_regex = rc

@Sheet.api
def highlight_input(sheet, cols=[]):
    r = vd.inputMultiple(regex=dict(prompt=f"highlight regex: ", type="regex", defaultLast=True, help=vd.help_regex),
                        flags=dict(prompt="regex flags: ", type="regex_flags", value=sheet.options.regex_flags, help=vd.help_regex_flags))
    if not sheet.options.highlight_search:
        vd.warning('`highlight_search` option needs to be set to True')
    sheet.setHighlightRegex(r, cols)

@Sheet.after
def clear_search(sheet):
    if not sheet.options.highlight_search:
        return
    for col in sheet.columns:
        if col.highlight_regex:
            vd.addUndo(setattr, col, 'highlight_regex', col.highlight_regex)
            col.highlight_regex = None
    if sheet.highlight_regex:
        vd.addUndo(setattr, sheet, 'highlight_regex', sheet.highlight_regex)
        sheet.highlight_regex = None

vd.option('highlight_search', True, 'whether to highlight strings in searches')
vd.option('color_highlight_search', '21 blue on 15 white', 'color to use for highlighting search results', sheettype=None)  #bright blue on white

Sheet.addCommand('', 'highlight-sheet', 'highlight_input(None)', 'highlight a regex in all columns')
Sheet.addCommand('', 'highlight-col', 'highlight_input([cursorCol])', 'highlight a regex in current column')
Sheet.addCommand('', 'highlight-clear', 'clear_search()', 'clear the current highlight pattern')
# redefine existing commands
Sheet.addCommand('r', 'search-keys', 'tmp=cursorVisibleColIndex; cols=keyCols or [visibleCols[0]]; r=moveInputRegex("row key", type="regex-row", columns=cols); setHighlightRegex(r, cols); sheet.cursorVisibleColIndex=tmp', 'go to next row with key matching regex')
Sheet.addCommand('/', 'search-col', 'r=moveInputRegex("search", columns="cursorCol", backward=False); setHighlightRegex(r, [cursorCol])', 'search for regex forwards in current column')
Sheet.addCommand('?', 'searchr-col', 'r=moveInputRegex("reverse search", columns="cursorCol", backward=True); setHighlightRegex(r, [cursorCol])', 'search for regex backwards in current column')
Sheet.addCommand('g/', 'search-cols', 'r=moveInputRegex("g/", backward=False, columns="visibleCols"); setHighlightRegex(r, sheet.visibleCols)', 'search for regex forwards over all visible columns')
Sheet.addCommand('g?', 'searchr-cols', 'r=moveInputRegex("g?", backward=True, columns="visibleCols"); setHighlightRegex(r, sheet.visibleCols)', 'search for regex backwards over all visible columns')

vd.addGlobals(highlight_chunks=highlight_chunks)
