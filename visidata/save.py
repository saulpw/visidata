from visidata import *


vd.option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
vd.option('safe_error', '#ERR', 'error string to use while saving', replay=True)
vd.option('disp_formatter', 'generic', 'formatter to use for display and saving', replay=True)

@Sheet.api
def safe_trdict(vs):
    'returns string.translate dictionary for replacing tabs and newlines'
    if options.safety_first:
        delim = vs.options.delimiter
        return {
             0: '', #  strip NUL completely
    ord(delim): vs.options.tsv_safe_tab, # \t
            10: vs.options.tsv_safe_newline,  # \n
            13: vs.options.tsv_safe_newline,  # \r
        }
    return {}


@Sheet.api
def iterdispvals(sheet, *cols, format=False):
    'For each row in sheet, yield OrderedDict of values for given cols.  Values are typed if format=False, or a formatted display string if format=True.'
    if not cols:
        cols = sheet.visibleCols

    transformers = collections.OrderedDict()  # list of transformers for each column in order
    for col in cols:
        transformers[col] = [ col.type ]
        if format:
            formatMaker = getattr(col, 'formatter_'+(col.formatter or sheet.options.disp_formatter))
            transformers[col].append(formatMaker(col._formatdict))
        trdict = sheet.safe_trdict()
        if trdict:
            transformers[col].append(lambda v,trdict=trdict: v.translate(trdict))

    options_safe_error = options.safe_error
    for r in Progress(sheet.rows):
        dispvals = collections.OrderedDict()  # [col] -> value
        for col, transforms in transformers.items():
            try:
                dispval = col.getValue(r)

            except Exception as e:
                vd.exceptionCaught(e)
                dispval = options_safe_error or str(e)

            try:
                for t in transforms:
                    if dispval is None:
                        break
                    elif isinstance(dispval, TypedExceptionWrapper):
                        dispval = options_safe_error or str(dispval)
                        break
                    else:
                        dispval = t(dispval)

                if dispval is None and format:
                    dispval = ''
            except Exception as e:
                dispval = str(dispval)

            dispvals[col] = dispval

        yield dispvals


@Sheet.api
def itervals(sheet, *cols, format=False):
    for row in sheet.iterdispvals(*cols, format=format):
        yield [row[c] for c in cols]

@BaseSheet.api
def getDefaultSaveName(sheet):
    src = getattr(sheet, 'source', None)
    if hasattr(src, 'scheme') and src.scheme:
        return src.name + src.suffix
    if isinstance(src, Path):
        if sheet.options.is_set('save_filetype', sheet):
            # if save_filetype is over-ridden from default, use it as the extension
            return str(src.with_suffix('')) + '.' + sheet.options.save_filetype
        return str(src)
    else:
        return sheet.name+'.'+getattr(sheet, 'filetype', options.save_filetype)


@VisiData.api
def save_cols(vd, cols):
    sheet = cols[0].sheet
    vs = copy(sheet)
    vs.columns = list(cols)
    vs.rows = sheet.rows
    if len(cols) == 1:
        savedcoltxt = cols[0].name + ' column'
    else:
        savedcoltxt = '%s columns' % len(cols)
    path = vd.inputPath('save %s to: ' % savedcoltxt, value=vs.getDefaultSaveName())
    vd.saveSheets(path, vs, confirm_overwrite=options.confirm_overwrite)


@VisiData.api
def saveSheets(vd, givenpath, *vsheets, confirm_overwrite=False):
    'Save all *vsheets* to *givenpath*.'

    filetype = givenpath.ext or options.save_filetype

    vd.clearCaches()

    savefunc = getattr(vsheets[0], 'save_' + filetype, None) or getattr(vd, 'save_' + filetype, None)

    if savefunc is None:
        vd.fail(f'no function to save as {filetype}')

    if givenpath.exists() and confirm_overwrite:
        vd.confirm("%s already exists. overwrite? " % givenpath.given)

    vd.status('saving %s sheets to %s as %s' % (len(vsheets), givenpath.given, filetype))

    if not givenpath.given.endswith('/'):  # forcibly specify save individual files into directory by ending path with /
        for vs in vsheets:
            vs.hasBeenModified = False
        # savefuncs(vd, p, *vsheets) will have 2 argcount (*vsheets does not get counted as an arg)
        # savefuncs(vd, p, vs) will have 3 argcount (vs counts as an arg, along with vd, path)
        if savefunc.__code__.co_argcount == 3 and len(vsheets) > 1:
            vd.fail(f'cannot save multiple {filetype} sheets to non-dir')
        return vd.execAsync(savefunc, givenpath, *vsheets)

    # path is a dir

    # save as individual files in the givenpath directory
    try:
        os.makedirs(givenpath, exist_ok=True)
    except FileExistsError:
        pass

    if not givenpath.is_dir():
        vd.fail(f'cannot save multiple {filetype} sheets to non-dir')

    def _savefiles(vsheets, givenpath, savefunc, filetype):
        for vs in vsheets:
            p = Path((givenpath / vs.name).with_suffix('.'+filetype))
            savefunc(p, vs)
            vs.hasBeenModified = False
    return vd.execAsync(_savefiles, vsheets, givenpath, savefunc, filetype)


@VisiData.api
def save_txt(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        for vs in vsheets:
            unitsep = vs.options.delimiter
            rowsep = vs.options.row_delimiter
            for dispvals in vs.iterdispvals(*vs.visibleCols, format=True):
                fp.write(unitsep.join(dispvals.values()))
                fp.write(rowsep)
    vd.status('%s save finished' % p)


@BaseSheet.api
def rootSheet(sheet):
    r = sheet
    while isinstance(r.source, BaseSheet):
        r = r.source

    return r

BaseSheet.addCommand('^S', 'save-sheet', 'vd.saveSheets(inputPath("save to: ", value=getDefaultSaveName()), sheet, confirm_overwrite=options.confirm_overwrite)', 'save current sheet to filename in format determined by extension (default .tsv)')
BaseSheet.addCommand('', 'save-source', 'vd.saveSheets(rootSheet().source, rootSheet(), confirm_overwrite=options.confirm_overwrite)', 'save root sheet to its source')
BaseSheet.addCommand('g^S', 'save-all', 'vd.saveSheets(inputPath("save all sheets to: "), *vd.stackedSheets, confirm_overwrite=options.confirm_overwrite)', 'save all sheets to given file or directory)')
IndexSheet.addCommand('g^S', 'save-selected', 'vd.saveSheets(inputPath("save %d sheets to: " % nSelectedRows, value="_".join(getattr(vs, "name", None) or "blank" for vs in selectedRows)), *selectedRows, confirm_overwrite=options.confirm_overwrite)', 'save all selected sheets to given file or directory')
Sheet.addCommand('', 'save-col', 'save_cols([cursorCol])', 'save current column only to filename in format determined by extension (default .tsv)')
Sheet.addCommand('', 'save-col-keys', 'save_cols(keyCols + [cursorCol])', 'save key columns and current column to filename in format determined by extension (default .tsv)')
