import functools
from visidata import vd, Progress

try:
    import tabulate
    for fmt in tabulate.tabulate_formats:
        def save_table(path, *sheets, fmt=fmt):
            import tabulate

            with path.open_text(mode='w', encoding=sheets[0].options.encoding) as fp:
                for vs in sheets:
                    fp.write(tabulate.tabulate(
                        vs.itervals(*vs.visibleCols, format=True),
                        headers=[ col.name for col in vs.visibleCols ],
                        tablefmt=fmt))

        if not getattr(vd, 'save_'+fmt, None):
            setattr(vd, 'save_'+fmt, save_table)
except ModuleNotFoundError:
    pass
