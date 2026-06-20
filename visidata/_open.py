import os
import os.path
import sys

from visidata import VisiData, vd, Path, BaseSheet, TableSheet, TextSheet, SettableColumn


vd.option('filetype', '', 'input filetype; overrides file extension', replay=True)

vd.stdinSource = None  # Path('-') with piped fp, set in main()


@VisiData.api
def inputFilename(vd, prompt, *args, **kwargs):
    completer= _completeFilename
    if not vd.couldOverwrite():  #1805 don't suggest an existing file
        completer = None
        v = kwargs.get('value', '')
        if v and Path(v).exists():
            kwargs['value'] = ''
    return vd.input(prompt, type="filename", *args, completer=completer, **kwargs).strip()


@VisiData.api
def inputPath(vd, *args, filetype='', **kwargs):
    'Input a path with filetype field. Sets filetype on the returned Path if given.'
    prompt = args[0] if args else kwargs.pop('prompt', 'path: ')
    completer = _completeFilename
    if not vd.couldOverwrite():  #1805
        completer = None
        v = kwargs.get('value', '')
        if v and Path(v).exists():
            kwargs['value'] = ''
    r = vd.inputMultiple(
        path=dict(prompt=prompt, type='filename', completer=completer, **kwargs),
        filetype=dict(prompt='as filetype: ', type='filetype', value=filetype),
    )
    p = Path(r['path'].strip())
    if r['filetype']:
        p.options.filetype = r['filetype']
    return p


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
def guessFiletype(vd, p, *args, funcprefix='guess_'):
    '''Call all vd.guess_<filetype>(p) functions and return best candidate sheet based on file contents.'''

    guessfuncs = [getattr(vd, x) for x in dir(vd) if x.startswith(funcprefix)]
    filetypes = []
    for f in guessfuncs:
        try:
            filetype = f(p, *args)
            if filetype:
                filetype['_guesser'] = f.__name__
                filetypes.append(filetype)
        except FileNotFoundError:
            pass
        except Exception as e:
            vd.debug(f'{f.__name__}: {e}')

    if filetypes:
        return sorted(filetypes, key=lambda r: -r.get('_likelihood', 1))[0]

    return {}


@VisiData.api
def guess_extension(vd, path):
    # try auto-detect from extension
    ext = path.suffix[1:].lower()
    openfunc = getattr(vd, f'open_{ext}', vd.getGlobals().get(f'open_{ext}'))
    if openfunc:
        return dict(filetype=ext, _likelihood=3)


@VisiData.api
def openPath(vd, p, filetype=None, create=False):
    '''Call ``open_<filetype>(p)`` or ``openurl_<p.scheme>(p, filetype)``.  Return constructed but unloaded sheet of appropriate type.
    If True, *create* will return a new, blank **Sheet** if file does not exist.'''
    filetype = filetype or p.options.filetype  # resolve from path instance, Path class, global  #1710

    if p.scheme and not p.has_fp():
        schemes = p.scheme.split('+')
        openfuncname = 'openurl_' + schemes[-1]

        openfunc = getattr(vd, openfuncname, None) or vd.getGlobals().get(openfuncname, None)
        if not openfunc:
            vd.fail(f'no loader for url scheme: {p.scheme}')

        return openfunc(p, filetype=filetype)

    if not p.exists() and not create:
        return None

    # assign filetype from extension, but only for files, not directories
    if not p.is_dir():  #2547
        filetype = filetype or p.ext

    filetype = filetype.lower()

    # store resolved filetype on path for downstream access (e.g. self.source.options.filetype)
    p.options.set('filetype', filetype, p, cmdlog=False)

    if not p.exists():
        newfunc = getattr(vd, 'new_' + filetype, vd.getGlobals().get('new_' + filetype))
        if not newfunc:
            vd.warning('%s does not exist, creating new sheet' % p)
            return vd.newSheet(p.base_stem, 1, source=p)

        vd.status('creating blank %s' % (p.given))
        return newfunc(p)

    if p.is_fifo() and not p.has_fp():
        # read the file as text, into a RepeatFile that can be opened multiple times
        p = Path(p.given, fp=p.open(mode='rb'))

    openfuncname = 'open_' + filetype
    openfunc = getattr(vd, openfuncname, vd.getGlobals().get(openfuncname))
    if not openfunc:
        opts = vd.guessFiletype(p)
        if opts and 'filetype' in opts:
            filetype = opts['filetype']
            openfuncname = 'open_' + filetype
            openfunc = getattr(vd, openfuncname, vd.getGlobals().get(openfuncname))
            if not openfunc:
                vd.error(f'guessed {filetype} but no {openfuncname}')

            vs = openfunc(p)
            for k, v in opts.items():
                if k != 'filetype' and not k.startswith('_'):
                    setattr(vs.options, k, v)
            vd.status(f'guessed `{opts["filetype"]}` filetype based on contents')
            return vs

        vd.warning(f'unknown `{filetype}` filetype')

        filetype = 'txt'
        openfunc = vd.open_txt

    vd.status('opening %s as %s' % (p.given, filetype))

    return openfunc(p)

@VisiData.api
def openSource(vd, p, filetype=None, create=False, **kwargs):
    '''Return unloaded sheet object for *p* opened as the given *filetype* and with *kwargs* as option overrides. *p* can be a Path or a string (filename, url, or "-" for stdin).
    when true, *create* will return a blank sheet, if file does not exist.'''

    if isinstance(p, BaseSheet):
        return p

    vs = None
    if isinstance(p, str):
        p = Path(p)

    if p.given == '-' and p.fp is None and p.fptext is None and vd.stdinSource is not None:
        p = vd.stdinSource  # bare Path('-') means piped stdin

    if p is vd.stdinSource:
        if p.fptext is None or p.fptext.isatty():
            vd.fail('cannot open stdin when it is a tty')
        vs = vd.openPath(p, filetype=filetype)
    else:
        vs = vd.openPath(p, filetype=filetype, create=create)

    for optname, optval in kwargs.items():
        vs.options[optname] = optval
        # Path is authoritative for format options  #2727
        if isinstance(vs.source, Path):
            vs.source.options.set(optname, optval, vs.source, cmdlog=False)

    return vs


#### enable external addons
@VisiData.api
def open_txt(vd, p):
    'Create sheet from `.txt` file at Path `p`, checking whether it is TSV.'
    if p.exists(): #1611
        with p.open(encoding=vd.options.encoding) as fp:
            delimiter = vd.options.delimiter
            try:
                if delimiter and delimiter in next(fp):    # peek at the first line
                    return vd.open_tsv(p)  # TSV often have .txt extension
            except StopIteration:
                return vd.newSheet(p.base_stem, 1, source=p)
    return TextSheet(p.base_stem, source=p)


BaseSheet.addCommand('o', 'open-file', 'vd.push(openSource(inputPath("open: "), create=True))', 'Open file or URL')
TableSheet.addCommand('zo', 'open-cell-file', 'cd=cursorDisplay; (vd.push(openSource(cd) if cd else fail("no path given")) or fail(f"file {cd} does not exist"))', 'Open file or URL from path in current cell')
BaseSheet.addCommand('gU', 'undo-last-quit', 'push(allSheets[-1])', 'reopen most recently closed sheet')

vd.addMenuItems('''
    File > Open > input file/url > open-file
    File > Reopen last closed > undo-last-quit
''')
