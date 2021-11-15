from visidata import vd, VisiData, Sheet, IndexSheet, SequenceSheet


@VisiData.api
def open_ods(vd, p):
    return OdsIndexSheet(p.name, source=p)


class OdsIndexSheet(IndexSheet):
    def iterload(self):
        import odf.opendocument
        import odf.table
        self.doc = odf.opendocument.load(self.source)
        for sheet in self.doc.spreadsheet.getElementsByType(odf.table.Table):
            yield OdsSheet(sheet.getAttribute('name'), source=sheet)


def _get_cell_string_value(cell, text_s):
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
        import odf.table
        import odf.text
        from odf.namespaces import TABLENS, OFFICENS
        from odf.text import S

        text_s = S().qname

        cell_names = [odf.table.CoveredTableCell().qname, odf.table.TableCell().qname]
        for odsrow in self.source.getElementsByType(odf.table.TableRow):
            row = []

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

                for _ in range(int(cell.attributes.get((TABLENS, "number-columns-repeated"), 1))):
                    row.append(value)

            for _ in range(int(odsrow.attributes.get((TABLENS, "number-rows-repeated"), 1))):
                yield list(row)
