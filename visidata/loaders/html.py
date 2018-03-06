import html
from visidata import *


def open_html(p):
    return HtmlTablesSheet(p.name, source=p)

# rowdef: lxml.html.HtmlElement
class HtmlTablesSheet(Sheet):
    rowtype = 'tables'
    columns = [
        Column('tag', getter=lambda col,row: row[0].tag),
        Column('id', getter=lambda col,row: row[0].attrib.get('id')),
        Column('nrows', type=int, getter=lambda col,row: len(row[1].rows)),
        Column('ncols', type=int, getter=lambda col,row: len(row[1].columns)),
        Column('classes', getter=lambda col,row: row[0].attrib.get('class')),

    ]
    commands = [ Command(ENTER, 'vd.push(cursorRow[1])', 'open this table') ]
    @async
    def reload(self):
        import lxml.html
        from lxml import etree
        utf8_parser = etree.HTMLParser(encoding='utf-8')
        with self.source.open_text() as fp:
            html = lxml.html.etree.parse(fp, parser=utf8_parser)
        self.rows = []
        for i, e in enumerate(html.iter('table')):
            if e.tag == 'table':
                vs = HtmlTableSheet(e.attrib.get("id", "table_" + str(i)), source=e)
                vs.reload()
                self.addRow((e, vs))

def is_header(elem):
    scope = elem.attrib.get('scope', '')

    if elem.tag == 'th':
        if not scope or scope == 'col':
            return True

    return False

class HtmlTableSheet(Sheet):
    rowtype = 'rows'
    columns = []

    @async
    def reload(self):
        self.rows = []
        headers = []
        for rownum, r in enumerate(self.source.iter('tr')):
            row = []

            colnum = 0
            # get starting column, which might be different if there were rowspan>1 already
            if rownum < len(headers):
                while colnum < len(headers[rownum]):
                    if headers[rownum][colnum] is None:
                        break
                    colnum += 1

            for cell in r.getchildren():
                colspan = int(cell.attrib.get('colspan', 1))
                rowspan = int(cell.attrib.get('rowspan', 1))
                cellval = ' '.join(cell.itertext()).strip()  # text only without markup

                if is_header(cell):
                    for k in range(rownum, rownum+rowspan):
                        while k >= len(headers):  # extend headers list with lists for all header rows
                            headers.append([])

                        for j in range(colnum, colnum+colspan):
                            while j >= len(headers[k]):
                                headers[k].append(None)
                            headers[k][j] = cellval
                        cellval = ''   # use empty non-None value for subsequent rows in the rowspan
                else:
                    while colnum >= len(row):
                        row.append(None)
                    row[colnum] = cellval

                colnum += colspan

            if any(row):
                self.addRow(row)

        self.columns = []
        if headers:
            for i, names in enumerate(itertools.zip_longest(*headers, fillvalue='')):
                self.addColumn(ColumnItem('_'.join(x for x in names if x), i))
        else:
            for i, name in enumerate(self.rows[0]):
                self.addColumn(ColumnItem(name, i))
            self.rows = self.rows[1:]

@async
def save_html(sheet, fn):
    'Save sheet as <table></table> in an HTML file.'

    with open(fn, 'w', encoding='ascii', errors='xmlcharrefreplace') as fp:
        fp.write('<table id="{sheetname}">\n'.format(sheetname=sheet.name))

        # headers
        fp.write('<tr>')
        for col in sheet.visibleCols:
            contents = html.escape(col.name)
            fp.write('<th>{colname}</th>'.format(colname=contents))
        fp.write('</tr>\n')

        # rows
        for r in Progress(sheet.rows):
            fp.write('<tr>')
            for col in sheet.visibleCols:
                fp.write('<td>')
                fp.write(html.escape(col.getDisplayValue(r)))
                fp.write('</td>')
            fp.write('</tr>\n')

        fp.write('</table>')
        status('%s save finished' % fn)



