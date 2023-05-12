from visidata import (
    ColumnItem,
    PythonSheet,
    VisiData,
    asyncthread,
    deduceType,
    vd,
)

try:
    # Python 3.11+
    import tomllib
except ModuleNotFoundError:
    # Python 3.10 and below
    tomllib = vd.importExternal("tomli")


@VisiData.api
def open_toml(vd, p):
    return TomlSheet(p.name, source=p)


class TomlSheet(PythonSheet):
    """A Sheet representing the top level of a loaded TOML file.

    This is an intentionally minimal loader with cues taken from
    VisiData built-in JSON and Python object sheet types.
    """

    rowtype = "values"  # rowdef: dict values, possibly nested

    @asyncthread
    def reload(self):
        """Loading a TOML file produces a single dict. Use
        its keys as column headings, and populate a single
        row.
        """
        self.columns = []
        self.rows = []

        data = tomllib.loads(self.source.read_text())
        for k, v in data.items():
            self.addColumn(ColumnItem(k, type=deduceType(v)))
        self.addRow(data)


vd.addGlobals(
    {
        "TomlSheet": TomlSheet,
    }
)
