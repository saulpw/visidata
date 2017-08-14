import random

from .vdtui import *

option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('headerlines', 1, 'parse first N rows of .csv/.tsv as column names')
option('filetype', '', 'specify file type')

command('+', 'cursorCol.aggregator = chooseOne(aggregators)', 'choose aggregator for this column')

# slide rows/columns around
command('H', 'moveVisibleCol(cursorVisibleColIndex, max(cursorVisibleColIndex-1, 0)); sheet.cursorVisibleColIndex -= 1', 'move this column one left')
command('J', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, min(cursorRowIndex+1, nRows-1))', 'move this row one down')
command('K', 'sheet.cursorRowIndex = moveListItem(rows, cursorRowIndex, max(cursorRowIndex-1, 0))', 'move this row one up')
command('L', 'moveVisibleCol(cursorVisibleColIndex, min(cursorVisibleColIndex+1, nVisibleCols-1)); sheet.cursorVisibleColIndex += 1', 'move this column one right')
command('gH', 'moveListItem(columns, cursorColIndex, nKeys)', 'move this column all the way to the left of the non-key columns')
command('gJ', 'moveListItem(rows, cursorRowIndex, nRows)', 'move this row all the way to the bottom')
command('gK', 'moveListItem(rows, cursorRowIndex, 0)', 'move this row all the way to the top')
command('gL', 'moveListItem(columns, cursorColIndex, nCols)', 'move this column all the way to the right')

command('c', 'searchColumnNameRegex(input("column name regex: ", "regex"))', 'go to visible column by regex of name')
command('r', 'sheet.cursorRowIndex = int(input("row number: "))', 'go to row number')

command('P', 'vd.push(copy("_sample")).rows = random.sample(rows, int(input("random population size: ")))', 'push duplicate sheet with a random sample of <N> rows')

command('a', 'rows.insert(cursorRowIndex+1, list((None for c in columns))); cursorDown(1)', 'insert a blank row')
command('^I',  'moveListItem(vd.sheets, 0, len(vd.sheets))', 'cycle through sheet stack') # TAB
command('KEY_BTAB', 'moveListItem(vd.sheets, -1, 0)', 'reverse cycle through sheet stack')
command('~', 'cursorCol.type = str', 'set column type to string')
command('@', 'cursorCol.type = date', 'set column type to ISO8601 datetime')
command('#', 'cursorCol.type = int', 'set column type to integer')
command('$', 'cursorCol.type = currency', 'set column type to currency')
command('%', 'cursorCol.type = float', 'set column type to float')

command('^', 'cursorCol.name = editCell(cursorVisibleColIndex, -1)', 'rename this column')
command('g^', 'for c in visibleCols: c.name = c.getDisplayValue(cursorRow)', 'set names of all visible columns to this row')
command('!', 'cursorRight(toggleKeyColumn(cursorColIndex))', 'toggle this column as a key column')
command('g[', 'rows.sort(key=lambda r,cols=keyCols: tuple(c.getValue(r) for c in cols))', 'sort by all key columns ascending')
command('g]', 'rows.sort(key=lambda r,cols=keyCols: tuple(c.getValue(r) for c in cols), reverse=True)', 'sort by all key columns descending')

command('o', 'vd.push(openSource(input("open: ", "filename")))', 'open local file or url')
command('^S', 'saveSheet(sheet, input("save to: ", "filename", value=str(sheet.source)))', 'save this sheet to new file')

def saveSheet(vs, fn):
    'Save sheet `vs` with given filename `fn`.'
    if Path(fn).exists():
        if options.confirm_overwrite:
            confirm('%s already exists. overwrite? ' % fn)

    basename, ext = os.path.splitext(fn)
    funcname = 'save_' + ext[1:]
    if funcname not in getGlobals():
        funcname = 'save_tsv'
    getGlobals().get(funcname)(vs, fn)
    status('saving to ' + fn)

class DirSheet(Sheet):
    'Sheet displaying directory, using ENTER to open a particular file.'

    def reload(self):
        'Populate sheet via `reload` function.'
        self.rows = [(p, p.stat()) for p in self.source.iterdir()]  #  if not p.name.startswith('.')]
        self.command(ENTER, 'vd.push(openSource(cursorRow[0]))', 'open file')  # path, filename
        self.columns = [Column('filename', str, lambda r: r[0].name + r[0].ext),
                      Column('type', str, lambda r: r[0].is_dir() and '/' or r[0].suffix),
                      Column('size', int, lambda r: r[1].st_size),
                      Column('mtime', date, lambda r: r[1].st_mtime)]


def openSource(p, filetype=None):
    'open a Path or a str (converts to Path or calls some TBD openUrl)'
    if isinstance(p, str):
        if '://' in p:
            filetype = url(p).schema.lower()
            openfunc = 'openurl_' + filetype
            vs = getGlobals()[openfunc](p)
        else:
            return openSource(Path(p), filetype)  # convert to Path and recurse
    elif isinstance(p, Path):
        if not filetype:
            filetype = options.filetype or p.suffix

        if os.path.isdir(p.resolve()):
            vs = DirSheet(p.name, p)
            filetype = 'dir'
        else:
            openfunc = 'open_' + filetype.lower()
            if openfunc not in getGlobals():
                status('no %s function' % openfunc)
                filetype = 'txt'
                openfunc = 'open_txt'
            vs = getGlobals()[openfunc](p)
    else:  # some other object
        status('unknown object type %s' % type(p))
        vs = None

    if vs:
        status('opening %s as %s' % (p.name, filetype))
    return vs

#### enable external addons
def open_vd(p):
    'Opens a .vd file as a .tsv file'
    vs = open_tsv(p)
    vs.reload()
    return vs

def open_py(p):
    'Load a .py addon into the global context.'
    contents = p.read_text()
    exec(contents, getGlobals())
    status('executed %s' % p)

def open_txt(p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if '\t' in next(fp):
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, p)

def _getTsvHeaders(fp, nlines):
    headers = []
    i = 0
    while i < nlines:
        L = next(fp)
        L = L[:-1]
        if L:
            headers.append(L.split('\t'))
            i += 1

    return headers

def open_tsv(p, vs=None):
    'Parse contents of Path `p` and populate columns.'

    if vs is None:
        vs = Sheet(p.name, p)
        vs.loader = lambda vs=vs: reload_tsv(vs)

    header_lines = int(options.headerlines)

    with vs.source.open_text() as fp:
        headers = _getTsvHeaders(fp, header_lines or 1)  # get one data line if no headers

        if header_lines == 0:
            vs.columns = ArrayColumns(len(headers[0]))
        else:
            # columns ideally reflect the max number of fields over all rows
            # but that's a lot of work for a large dataset
            vs.columns = ArrayNamedColumns('\\n'.join(x) for x in zip(*headers[:header_lines]))

    return vs

@async
def reload_tsv(vs):
    'Asynchronous wrapper for `reload_tsv_sync`.'
    reload_tsv_sync(vs)

def reload_tsv_sync(vs):
    'Perform synchronous loading of TSV file, discarding header lines.'
    header_lines = int(options.headerlines)

    vs.rows = []
    with vs.source.open_text() as fp:
        _getTsvHeaders(fp, header_lines)  # discard header lines

        vs.progressMade = 0
        vs.progressTotal = vs.source.filesize
        for L in fp:
            L = L[:-1]
            if L:
                vs.rows.append(L.split('\t'))
            vs.progressMade += len(L)

    vs.progressMade = 0
    vs.progressTotal = 0

    status('loaded %s' % vs.name)


@async
def save_tsv(vs, fn):
    'Write sheet to file `fn` as TSV, reporting progress on status bar.'
    with open(fn, 'w', encoding=options.encoding, errors=options.encoding_errors) as fp:
        colhdr = '\t'.join(col.name for col in vs.visibleCols) + '\n'
        if colhdr.strip():  # is anything but whitespace
            fp.write(colhdr)
        for r in vs.genProgress(vs.rows):
            fp.write('\t'.join(col.getDisplayValue(r) for col in vs.visibleCols) + '\n')
    status('%s save finished' % fn)

