"""
Filename: vdfec.py
Version: 0.0.0
Last updated: 2019-04-21
Home: https://github.com/jsvine/visidata-plugins
Author: Jeremy Singer-Vine

# Installation

- Install fecfile: `pip install fecfile`
- Add vdfec.py to your ~/.visidata directory
- Add "import vdfec" to your ~/.visidatarc file

# Usage

vdfec.py enables VisiData to load .fec files from the Federal Election Commission.

Once saved to your ~/.visidata directory, and imported via your ~/.visidatarc file,
you should be able to interactively explore .fec files as you would any other 
filetype in VisiData.

From the command line:

    vd path/to/my/file.fec

# Thanks

vdfec.py depends heavily on Evan Sonderegger's `fecfile` Python library: https://esonderegger.github.io/fecfile/

... which in turn is based on Derek Willis's `Fech` Ruby library: https://github.com/dwillis/Fech

... and Chris Zubak-Skees' transformation of `Fech`'s form-and-field mappings: https://github.com/PublicI/fec-parse/blob/master/lib/renderedmaps.js

Thanks to all who have contributed to those projects.

"""

from visidata import (
    vd,
    Path,
    Sheet,
    TextSheet,
    joinSheetnames,
    Column,
    ColumnAttr,
    ColumnItem,
    ENTER,
    asyncthread,
    copy,
    status,
    warning,
    Progress,
    addGlobals,
)

class DiveSheet(Sheet):
    "A deeply-diveable, quick-diving sheet."

    def reload(self):
        mapping = self.source

        self.columns = []
        self.rows = []

        self.key_type = str
        self.size = len(mapping)

        if self.size == 0:
            return

        if isinstance(mapping, list):
            first = mapping[0]
            if isinstance(first, dict):
                colgetter = lambda x: x.keys()
            elif isinstance(first, list):
                colgetter = lambda x: list(range(len(x)))
            else:
                mapping = dict(enumerate(mapping))
                self.key_type = int
                self.size = len(mapping)

        if isinstance(mapping, dict):
            self.is_keyvalue = True
            if self.size:
                max_key_len = max(map(len, map(str, mapping.keys())))
                key_width = min(50, max(max_key_len + 2, 6))
            else:
                key_width = None

            self.addColumn(ColumnItem(
                "key",
                width = key_width,
                type = self.key_type
            ))
            self.addColumn(ColumnItem("value"))
            self.setKeys(self.columns[:1])

            for k, v in mapping.items():
                self.addRow({ "key": k, "value": v })

        elif isinstance(mapping, list):
            self.is_keyvalue = False
            indices = [] 
            for item in mapping:
                try:
                    cols = colgetter(item)
                    for col in cols:
                        if col not in indices:
                            self.addColumn(ColumnItem(col))
                            indices.append(col)

                    self.addRow(item)

                except Exception as e:
                    warning("Can't dive on lists with heterogenous item types.")
                    return False

    def dive(self):
        if self.is_keyvalue:
            cell = self.cursorRow["value"]
            name = joinSheetnames(self.name, self.cursorRow["key"])

            if isinstance(cell, (list, dict)):
                vs = self.__class__(name, source = cell)
            else:
                warning("Nothing to dive into.")
                return
        else:
            name = joinSheetnames(self.name, "row")
            vs = self.__class__(name, source = self.cursorRow)

        success = vs.reload()
        if success == False:
            return

        vd.push(vs)

DiveSheet.addCommand(
    ENTER,
    'dive-row',
    'vd.sheet.dive()'
)

class FECItemizationSheet(Sheet):
    "A sheet to display a list of FEC itemizations from a given form/schedule."

    rowtype = "itemizations"

    @asyncthread
    def reload(self):
        self.rows = []
        self.columns = []

        if len(self.source) == 0:
            return

        for i, row in enumerate(Progress(self.source, total = len(self.source))):
            if i == 0:
                self.set_columns_from_row(row)
            self.addRow(row)
    
    def set_columns_from_row(self, row):
        self.columns.clear()
        for i, name in enumerate(row.keys()):
            self.addColumn(ColumnItem(name))
    def dive(self):
        vs = DiveSheet(
            joinSheetnames(self.name, "detail"),
            source = self.cursorRow
        )
        vs.reload()
        vd.push(vs)

FECItemizationSheet.addCommand(
    ENTER,
    'dive-row',
    'vd.sheet.dive()'
)

class FECScheduleSheet(Sheet):
    "A sheet to display the list of itemized schedules in a filing."

    rowtype = "schedules"

    columns = [
        ColumnAttr("schedule", "schedule_name", width = 14),
        ColumnAttr("name", width = 0),
        ColumnAttr("size", type = int),
    ]

    nKeys = 1

    @asyncthread
    def reload(self):
        self.rows = []

        for schedule_name in self.source.keys():
            vs = FECItemizationSheet(
                joinSheetnames(self.name, schedule_name),
                schedule_name = schedule_name,
                source = self.source[schedule_name],
                size = len(self.source[schedule_name]),
            )
            self.addRow(vs)

FECScheduleSheet.addCommand(
    ENTER,
    'dive-row',
    'vd.push(cursorRow)'
)

COMPONENT_SHEET_CLASSES = {
    "header": DiveSheet,
    "summary": DiveSheet,
    "itemization": FECScheduleSheet,
    "text": FECItemizationSheet,
    "F99_text": TextSheet,
}

class FECFiling(Sheet):
    "A sheet representing an entire .fec file."

    rowtype = "components"
    filing = None

    columns = [
        ColumnAttr("component", "component_name", width = 14),
        ColumnAttr("name", width = 0),
        ColumnAttr("size", type = int),
    ]

    nKeys = 1

    @asyncthread
    def reload(self):
        from fecfile import fecparser
        self.rows = []

        row_dict = { }
        itemization_subsheets = {}

        def addSheetRow(component_name):
            "On first encountering a component, add a row to the filing sheet"

            cls = COMPONENT_SHEET_CLASSES[component_name]

            source_cls = list if cls in [
                    FECItemizationSheet,
                    TextSheet
                ] else dict

            vs = cls(
                joinSheetnames(self.name, component_name),
                component_name = component_name,
                source = source_cls(),
                size = 0,
            )

            vs.reload()
            row_dict[component_name] = vs
            self.addRow(vs)

        src = Path(self.source.resolve())

        item_iter = fecparser.iter_lines(src, { "as_strings": True })

        for item in item_iter:
            dtype = item.data_type 
            if dtype not in row_dict.keys():
                addSheetRow(dtype)

            sheet_row = row_dict[dtype]

            if dtype in [ "header", "summary" ]:
                sheet_row.source = item.data
                sheet_row.reload()

            elif dtype == "text":
                if len(sheet_row.source) == 0:
                    sheet_row.set_columns_from_row(item.data)
                sheet_row.source.append(item.data)
                sheet_row.addRow(item.data)
                sheet_row.size += 1

            elif dtype == "F99_text":
                sheet_row.source = item.data.split("\n")
                sheet_row.size = len(sheet_row.source)

            elif dtype == "itemization":
                form_type = item.data["form_type"]

                if form_type[0] == "S":
                    form_type = "Schedule " + item.data["form_type"][1]

                if form_type not in sheet_row.source:
                    sheet_row.source[form_type] = [ ] 
                    subsheet = FECItemizationSheet(
                        joinSheetnames(sheet_row.name, form_type),
                        schedule_name = form_type,
                        source = [ ],
                        size = 0,
                    )
                    subsheet.reload()
                    subsheet.set_columns_from_row(item.data)
                    sheet_row.addRow(subsheet)
                    itemization_subsheets[form_type] = subsheet
                else:
                    subsheet = itemization_subsheets[form_type]

                subsheet.addRow(item.data)
                subsheet.source.append(item.data)
                subsheet.size += 1

                sheet_row.source[form_type].append(item.data)
                sheet_row.size += 1

FECFiling.addCommand(
    ENTER,
    'dive-row',
    'vd.push(cursorRow)'
)

def open_fec(p):
    return FECFiling(p.name, source=p)

addGlobals({
    "open_fec": open_fec,
    "DiveSheet": DiveSheet
})
