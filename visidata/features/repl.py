"""
Launch an embedded ptipython REPL from within VisiData.
Contributed by @ajkerrigan #2290 #2736
"""

from pathlib import Path

from visidata import LazyChainMap, Sheet, SuspendCurses, VisiData


# Sheet-local properties that are expensive or problematic during
# tab-completion in the REPL.  Override them with inert values.
_REPL_OVERRIDES = dict(
    replayStatus="dummy",
    someSelectedRows="dummy",
    onlySelectedRows="dummy",
)


class _LazyNamespace(dict):
    'dict backed by a LazyChainMap; evaluates attributes lazily on access.'
    def __init__(self, lcm):
        # Seed dict keys so IPython tab-completion discovers names,
        # but values are sentinel and resolved on first __getitem__.
        super().__init__({k: _SENTINEL for k in lcm})
        self._lcm = lcm

    def __getitem__(self, k):
        v = super().__getitem__(k)
        if v is _SENTINEL:
            v = self._lcm[k]
            super().__setitem__(k, v)
        return v

    def __contains__(self, k):
        return super().__contains__(k) or k in self._lcm

_SENTINEL = object()


@VisiData.api
def openRepl(vd):
    """Open a ptipython-based REPL that inherits VisiData's context."""
    ptipython = vd.importExternal('ptpython.ipython', 'ptpython')

    def configure(python_input):
        python_input.title = "VisiData IPython REPL (ptipython)"

    lcm = LazyChainMap(vd.sheet, locals=vd.getGlobals())
    user_ns = _LazyNamespace(lcm)
    user_ns.update(_REPL_OVERRIDES)

    with SuspendCurses():
        try:
            history_file = (
                Path(vd.options.visidata_dir).expanduser()
                / "cache"
                / "ptpython"
                / "history"
            )
            Path.mkdir(history_file.parent, parents=True, exist_ok=True)
            ptipython.embed(
                user_ns=user_ns,
                history_filename=str(history_file),
                vi_mode=True,
                configure=configure,
                title="VisiData IPython REPL (ptipython)",
            )
        except Exception as e:
            vd.exceptionCaught(e)
        finally:
            # The embedded IPython session is a singleton by default,
            # but launching it via `open-repl` in VisiData a second time
            # seems to either freeze or leave an exit message up from the
            # previous instance. Clean out the existing instance so any
            # future invocations get a fresh start.
            ptipython.InteractiveShellEmbed.clear_instance()


Sheet.addCommand("", "open-repl", "vd.openRepl()")
