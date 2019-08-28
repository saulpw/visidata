import html
from visidata import *


def open_html(p):
    return HtmlTablesSheet(p.name, source=p)
open_htm = open_html


class HtmlTablesSheet(IndexSheet):
    rowtype = 'sheets'  # rowdef: HtmlTableSheet (sheet.html = lxml.html.HtmlElement)
    columns = IndexSheet.columns + [
        Column('tag', width=0, getter=lambda col,row: row.html.tag),
        Column('id', getter=lambda col,row: row.html.attrib.get('id')),
        Column('classes', getter=lambda col,row: row.html.attrib.get('class')),
    ]
    @asyncthread
    def reload(self):
        import lxml.html
        from lxml import etree
        utf8_parser = etree.HTMLParser(encoding='utf-8')
        with self.source.open_text() as fp:
            html = lxml.html.etree.parse(fp, parser=utf8_parser)
        self.rows = []
        self.column('name').keycol = True
        self.column('keys').hide()
        self.column('source').hide()

        for i, e in enumerate(html.iter('table')):
            if e.tag == 'table':
                vs = HtmlTableSheet(e.attrib.get("id", "table_" + str(i)), source=e)
                vs.reload()
                vs.html = e
                self.addRow(vs)

HtmlTablesSheet.addCommand(ENTER, 'dive-row', 'vd.push(cursorRow)')

def is_header(elem):
    scope = elem.attrib.get('scope', '')

    if elem.tag == 'th':
        if not scope or scope == 'col':
            return True

    return False

class HtmlTableSheet(Sheet):
    rowtype = 'rows'
    columns = []

    @asyncthread
    def reload(self):
        self.rows = []
        headers = []

        maxlinks = {}  # [colnum] -> nlinks:int

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
                cellval = ' '.join(x.strip() for x in cell.itertext())  # text only without markup
                links = [x.get('href') for x in cell.iter('a')]
                maxlinks[colnum] = max(maxlinks.get(colnum, 0), len(links))

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
                    row[colnum] = (cellval, links)

                colnum += colspan

            if any(row):
                self.addRow(row)

        self.columns = []
        if headers:
            it = itertools.zip_longest(*headers, fillvalue='')
        else:
            it = [list(x) for x in self.rows[0]]
            self.rows = self.rows[1:]

        for colnum, names in enumerate(it):
            name = '_'.join(str(x) for x in names if x)
            self.addColumn(Column(name, getter=lambda c,r,i=colnum: r[i][0]))
            for linknum in range(maxlinks.get(colnum, 0)):
                self.addColumn(Column(name+'_link'+str(linknum), width=20, getter=lambda c,r,i=colnum,j=linknum: r[i][1][j]))


def save_html(p, *vsheets):
    'Save vsheets as HTML tables in a single file'

    with open(p, 'w', encoding='ascii', errors='xmlcharrefreplace') as fp:
        for sheet in vsheets:

            fp.write('<h2 class="sheetname">%s</h2>\n'.format(sheetname=html.escape(sheet.name)))

            fp.write('<table id="{sheetname}">\n'.format(sheetname=html.escape(sheet.name)))

            # headers
            fp.write('<tr>')
            for col in sheet.visibleCols:
                contents = html.escape(col.name)
                fp.write('<th>{colname}</th>'.format(colname=contents))
            fp.write('</tr>\n')

            # rows
            for r in Progress(sheet.rows, 'saving'):
                fp.write('<tr>')
                for col in sheet.visibleCols:
                    fp.write('<td>')
                    fp.write(html.escape(col.getDisplayValue(r)))
                    fp.write('</td>')
                fp.write('</tr>\n')

            fp.write('</table>')
            status('%s save finished' % p)


save_htm = multisave_htm = multisave_html = save_html
