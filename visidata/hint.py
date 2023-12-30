import collections

from visidata import vd, BaseSheet


@BaseSheet.lazy_property
def prevHints(sheet):
    return collections.defaultdict(int)


@BaseSheet.api
def getHint(sheet, *args, **kwargs) -> str:
    funcs = [getattr(sheet, x) for x in dir(sheet) if x.startswith('hint_')]
    results = []
    hints = sheet.prevHints
    for f in funcs:
        try:
            r = f(*args, **kwargs)
            if r:
                if isinstance(r, dict):
                    n = r.get('_relevance', 1)
                    v = r
                elif isinstance(r, tuple):
                    n, v = r
                else:
                    n = 1
                    v = r

                if v not in sheet.prevHints:
                    results.append((n, v))
                    sheet.prevHints[v] += 1
        except Exception as e:
            vd.debug(f'{f.__name__}: {e}')

    if results:
        return sorted(results, reverse=True)[0][1]


vd.addCommand('', 'help-hint', 'status(getHint() or pressMenu("Help"))', 'get context-dependent hint on what to do next')
