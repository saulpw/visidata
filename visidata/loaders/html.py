import html
from visidata import *


def open_html(p):
    return HtmlTablesSheet(p.name, source=p)

# rowdef: lxml.html.HtmlElement
class HtmlTablesSheet(Sheet):
    rowtype = 'tables'
    columns = [
        Column('tag', getter=lambda col,row: row.tag),
        Column('id', getter=lambda col,row: row.attrib.get('id')),
        Column('classes', getter=lambda col,row: row.attrib.get('class')),
    ]
    commands = [ Command(ENTER, 'vd.push(HtmlTableSheet(name=cursorRow.attrib.get("id", "table_" + str(cursorRowIndex)), source=cursorRow))', 'open this table') ]
    @async
    def reload(self):
        import lxml.html
        from lxml import etree
        utf8_parser = etree.HTMLParser(encoding='utf-8')
        with self.source.open_text() as fp:
            html = lxml.html.etree.parse(fp, parser=utf8_parser)
        self.rows = []
        for e in html.iter():
            if e.tag == 'table':
                self.addRow(e)

class HtmlTableSheet(Sheet):
    rowtype = 'rows'
    columns = []

    @async
    def reload(self):
        self.rows = []
        for r in self.source.iter():
            if r.tag == 'tr':
                row = [(c.text or '').strip() for c in r.getchildren()]
                if any(row):
                    self.addRow(row)
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



