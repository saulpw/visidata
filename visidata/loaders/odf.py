from visidata import vd, VisiData, Sheet, IndexSheet, SequenceSheet


@VisiData.api
def open_ods(vd, p):
    return OdsIndexSheet(p.base_stem, source=p)


class OdsIndexSheet(IndexSheet):
    def iterload(self):
        vd.importExternal('odf', 'odfpy')
        import odf.opendocument
        import odf.table
        self.doc = odf.opendocument.load(self.source)
        for sheet in self.doc.spreadsheet.getElementsByType(odf.table.Table):
            yield OdsSheet(sheet.getAttribute('name'), source=sheet)


def _get_cell_string_value(cell, text_s):
        vd.importExternal('odf', 'odfpy')
        from odf.element import Element
        from odf.namespaces import TEXTNS

        value = ''

        for fragment in cell.childNodes:
            if isinstance(fragment, Element):
                if fragment.qname == text_s:
                    value += " " * int(fragment.attributes.get((TEXTNS, "c"), 1))
                else:
                    value += _get_cell_string_value(fragment, text_s)
            else:
                value += str(fragment)
        return value


class OdsSheet(SequenceSheet):
    def iterload(self):
        vd.importExternal('odf', 'odfpy')
        import odf.table
        import odf.text
        from odf.namespaces import TABLENS, OFFICENS
        from odf.text import S

        text_s = S().qname

        cell_names = [odf.table.CoveredTableCell().qname, odf.table.TableCell().qname]
        empty_rows = 0
        for odsrow in self.source.getElementsByType(odf.table.TableRow):
            row = []

            empty_cells = 0
            for cell in odsrow.childNodes:
                if cell.qname not in cell_names: continue
                value = ''
                if cell.qname == odf.table.TableCell().qname:
                    cell_type = cell.attributes.get((OFFICENS, "value-type"))
                    if cell_type is None:
                        value = None
                    elif cell_type == "boolean":
                        value = str(cell) == "TRUE"
                    elif cell_type in ["float", "percentage", 'currency']:
                        value = cell.attributes.get((OFFICENS, "value"))
                    elif cell_type == "date":
                        value = cell.attributes.get((OFFICENS, "date-value"))
                    elif cell_type == "string":
                        value = _get_cell_string_value(cell, text_s)
                    else:
                        value = str(cell)

                column_repeat = int(cell.attributes.get((TABLENS, "number-columns-repeated"), 1))
                if value is None:
                    empty_cells += column_repeat
                else:
                    row.extend([""] * empty_cells)
                    empty_cells = 0
                    row.extend([value]*column_repeat)

            row_repeat = int(odsrow.attributes.get((TABLENS, "number-rows-repeated"), 1))
            if len(row) == 0:
                empty_rows += row_repeat
            else:
                for i in range(empty_rows):
                    yield []
                empty_rows = 0
                for i in range(row_repeat):
                    yield list(row)
