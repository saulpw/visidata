from . import FileBrowser, TextViewer
from . import status
from .Path import Path

### input formats and helpers

sourceCache = {}

def getTextContents(p):
    if not p in sourceCache:
        sourceCache[p] = p.read_text(encoding=options.encoding, errors=options.encoding_errors)
    return sourceCache[p]

def open_source(p, filetype=None):
    if isinstance(p, Path):
        if filetype is None:
            filetype = p.suffix

        if p.is_dir():
            vs = FileBrowser(p)
        else:
            openfunc = 'open_' + filetype
            if openfunc not in globals():
                openfunc = 'open_txt'
                status('no %s function' % openfunc)
            vs = globals()[openfunc](p)
    elif isinstance(p, str):
        if '://' in p:
            vs = openUrl(p)
        else:
            return open_source(Path(p), filetype)
    else:  # some other object
        status('unknown object type %s' % type(p))
        vs = None

    if vs:
        status('opened %s' % p.name)
    return vs

def open_txt(p):
    contents = getTextContents(p)
    if '\t' in contents[:32]:
        return open_tsv(p)  # TSV often have .txt extension
    return TextViewer(p.name, contents, p)

def open_json(p):
    import json
    return load_pyobj(p.name, json.loads(getTextContents(p)))

#### external addons
def open_py(p):
    contents = getTextContents(p)
    exec(contents, globals())
    status('executed %s' % p)
