from visidata import (
    ColumnItem,
    PythonSheet,
    VisiData,
    asyncthread,
    deduceType,
    vd,
)


@VisiData.api
def open_toml(vd, p):
    return TomlSheet(p.base_stem, source=p)


class TomlSheet(PythonSheet):
    """A Sheet representing the top level of a loaded TOML file.

    This is an intentionally minimal loader with cues taken from
    VisiData built-in JSON and Python object sheet types.
    """
    guide = '''# Toml Sheet
This sheet represents the top level of {sheet.source.name}.{sheet.source.ext}.

Each cell within this sheet can contain dictionaries (representing TOML key:value pairs), lists (representing TOML arrays), or scalars.

Some helpful commands when working with cells of lists and dictionaries:

- `(` (`expand-col`) on a column with lists or dictionaries will "expand" the structures in the cells into new columns within the current sheet.
- `zEnter` on a cell with lists or dictionaries will "dive" into the current cell, expanding its structures into rows and columns in a separate sheet.
'''

    rowtype = "values"  # rowdef: dict values, possibly nested

    def loader(self):
        """Loading a TOML file produces a single dict. Use
        its keys as column headings, and populate a single
        row.
        """
        self.columns = []
        self.rows = []

        try:
            # Python 3.11+
            import tomllib
        except ModuleNotFoundError:
            # Python 3.10 and below
            tomllib = vd.importExternal("tomli")

        data = tomllib.loads(self.source.read_text())
        for k, v in data.items():
            self.addColumn(ColumnItem(k, type=deduceType(v)))
        self.addRow(data)


vd.addGlobals(
    {
        "TomlSheet": TomlSheet,
    }
)
