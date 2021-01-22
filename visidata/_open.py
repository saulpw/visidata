from visidata import *

__all__ = ['open_txt']


option('filetype', '', 'specify file type', replay=True)


@VisiData.api
def inputFilename(vd, prompt, *args, **kwargs):
    return vd.input(prompt, type="filename", *args, completer=_completeFilename, **kwargs)


@VisiData.api
def inputPath(vd, *args, **kwargs):
    return Path(vd.inputFilename(*args, **kwargs))


def _completeFilename(val, state):
    i = val.rfind('/')
    if i < 0:  # no /
        base = ''
        partial = val
    elif i == 0: # root /
        base = '/'
        partial = val[1:]
    else:
        base = val[:i]
        partial = val[i+1:]

    files = []
    for f in os.listdir(Path(base or '.')):
        if f.startswith(partial):
            files.append(os.path.join(base, f))

    files.sort()
    return files[state%len(files)]


@VisiData.api
def openPath(vd, p, filetype=None, create=False):
    '''Call ``open_<filetype>(p)`` or ``openurl_<p.scheme>(p, filetype)``.  Return constructed but unloaded sheet of appropriate type.
    If True, *create* will return a new, blank **Sheet** if file does not exist.'''
    if p.scheme and not p.fp: # isinstance(p, UrlPath):
        openfunc = 'openurl_' + p.scheme
        try:
            return vd.getGlobals()[openfunc](p, filetype=filetype)
        except KeyError:
            vd.fail(f'no loader for url scheme: {p.scheme}')

    if not filetype:
        if p.is_dir():
            filetype = 'dir'
        else:
            filetype = p.ext or options.filetype or 'txt'

    if not p.exists():
        if not create:
            return None
        vd.warning('%s does not exist, creating new sheet' % p)
        return vd.newSheet(p.name, 1, source=p)

    filetype = filetype.lower()

    openfunc = getattr(vd, 'open_' + filetype, vd.getGlobals().get('open_' + filetype))
    if not openfunc:
        vd.warning('unknown "%s" filetype' % filetype)
        filetype = 'txt'
        openfunc = vd.getGlobals().get('open_txt')

    vd.status('opening %s as %s' % (p.given, filetype))
    return openfunc(p)


@VisiData.global_api
def openSource(vd, p, filetype=None, create=False, **kwargs):
    '''Return unloaded sheet object for *p* opened as the given *filetype* and with *kwargs* as option overrides. *p* can be a Path or a string (filename, url, or "-" for stdin).
    when true, *create* will return a blank sheet, if file does not exist.'''
    if not filetype:
        filetype = options.getonly('filetype', 'global', '')

    vs = None
    if isinstance(p, str):
        if '://' in p:
            vs = vd.openPath(Path(p), filetype=filetype)  # convert to Path and recurse
        elif p == '-':
            vs = vd.openPath(Path('-', fp=vd._stdin), filetype=filetype)
        else:
            vs = vd.openPath(Path(p), filetype=filetype, create=create)  # convert to Path and recurse
    else:
        vs = vs or vd.openPath(p, filetype=filetype, create=create)

    for optname, optval in kwargs.items():
        vs.options[optname] = optval

    return vs


#### enable external addons
def open_txt(p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    with p.open_text() as fp:
        if options.delimiter in next(fp):    # peek at the first line
            return open_tsv(p)  # TSV often have .txt extension
        return TextSheet(p.name, source=p)


@VisiData.api
def loadInternalSheet(vd, cls, p, **kwargs):
    'Load internal sheet of given class.  Internal sheets are always tsv.'
    vs = cls(p.name, source=p, **kwargs)
    options._set('encoding', 'utf8', vs)
    if p.exists():
        vd.sheets.insert(0, vs)
        vs.reload.__wrapped__(vs)
        vd.sheets.pop(0)
    return vs


BaseSheet.addCommand('o', 'open-file', 'vd.push(openSource(inputFilename("open: "), create=True))', 'open input in VisiData')
