from visidata import *


option('confirm_overwrite', True, 'whether to prompt for overwrite confirmation on save')
option('safe_error', '#ERR', 'error string to use while saving', replay=True)

@Sheet.api
def safe_trdict(vs):
    'returns string.translate dictionary for replacing tabs and newlines'
    if options.safety_first:
        delim = options.get('delimiter', vs)
        return {
             0: '', #  strip NUL completely
    ord(delim): options.get('tsv_safe_tab', vs), # \t
            10: options.get('tsv_safe_newline', vs),  # \n
            13: options.get('tsv_safe_newline', vs),  # \r
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
            transformers[col].append(
                # optimization: only lookup fmtstr once (it may have to get an option value)
                lambda v,fmtfunc=getType(col.type).formatter,fmtstr=col.fmtstr: fmtfunc(fmtstr, '' if v is None else v)
            )
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
                exceptionCaught(e)
                dispval = options_safe_error or str(e)

            try:
                for t in transforms:
                    if dispval is None:
                        dispval = ''
                        break
                    dispval = t(dispval)
            except Exception as e:
                dispval = str(dispval)

            dispvals[col] = dispval

        yield dispvals


@Sheet.api
def getDefaultSaveName(sheet):
    src = getattr(sheet, 'source', None)
    if isinstance(src, Path):
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
    path = inputPath('save %s to: ' % savedcoltxt, value=vs.getDefaultSaveName())
    vd.saveSheets(path, vs, confirm_overwrite=options.confirm_overwrite)


@VisiData.global_api
def saveSheets(vd, givenpath, *vsheets, confirm_overwrite=False):
    'Save all vsheets to givenpath'

    filetype = givenpath.ext or options.save_filetype

    if len(vsheets) > 1:
        if givenpath.exists() and confirm_overwrite:
            confirm("overwrite multiple? ")

        if not givenpath.given.endswith('/'):  # forcibly specify save individual files into directory by ending path with /
            savefunc = getGlobals().get('multisave_' + filetype, None)
            if savefunc:
                # use specific multisave function
                vd.execAsync(savefunc, givenpath, *vsheets)

        # more than one sheet; either no specific multisave for save filetype, or path ends with /

        # save as individual files in the givenpath directory
        try:
            os.makedirs(givenpath, exist_ok=True)
        except FileExistsError:
            pass

        assert givenpath.is_dir(), filetype + ' cannot save multiple sheets to non-dir'

        globalsavefunc = getGlobals().get('save_' + filetype)

        # get save function to call
        status('saving %s sheets to %s' % (len(vsheets), givenpath.given))
        for vs in vsheets:
            savefunc = getattr(vs, 'save_'+filetype, None)
            if not savefunc:
                savefunc = lambda p,vs=vs,f=globalsavefunc: f(p, vs)
            if savefunc:
                vd.execAsync(savefunc, givenpath.with_suffix('.'+filetype))
            else:
                warning('no function to save %s as type %s' % (vs, filetype))
    else:
        if givenpath.exists() and confirm_overwrite:
            confirm("%s already exists. overwrite? " % givenpath.given)

        # get save function to call
        savefunc = getattr(vsheets[0], 'save_'+filetype, None)
        if not savefunc:
            f = getGlobals().get('save_' + filetype) or fail('no function save_'+filetype)
            savefunc = lambda p,vs=vsheets[0],f=f: f(p, vs)

        status('saving to %s as %s' % (givenpath.given, filetype))
        vd.execAsync(savefunc, givenpath)


def save_txt(p, *vsheets):
    with p.open_text(mode='w') as fp:
        for vs in vsheets:
            col = vs.visibleCols[0]
            for dispvals in vs.iterdispvals(col, format=True):
                fp.write(dispvals[col] or '')
                fp.write('\n')
    status('%s save finished' % p)


multisave_txt = save_txt

Sheet.addCommand('^S', 'save-sheet', 'saveSheets(inputPath("save to: ", value=getDefaultSaveName()), sheet, confirm_overwrite=options.confirm_overwrite)')
globalCommand('g^S', 'save-all', 'saveSheets(inputPath("save all sheets to: "), *vd.sheets, confirm_overwrite=options.confirm_overwrite)')
Sheet.addCommand('z^S', 'save-col', 'save_cols([cursorCol])')
Sheet.addCommand('', 'save-col-keys', 'save_cols(keyCols + [cursorCol])')
