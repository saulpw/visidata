import html
import copy
import itertools

from visidata import VisiData, vd, Sheet, options, Column, Progress, IndexSheet, ItemColumn, InferColumnsSheet

vd.option('html_title', '<h2>{sheet.name}</h2>', 'table header when saving to html')

@VisiData.api
def open_html(vd, p):
    return HtmlTablesSheet(p.name, source=p)

VisiData.open_htm = VisiData.open_html

class HtmlTablesSheet(IndexSheet):
    rowtype = 'sheets'  # rowdef: HtmlTableSheet (sheet.html = lxml.html.HtmlElement)
    columns = IndexSheet.columns + [
        Column('tag', width=0, getter=lambda col,row: row.html.tag),
        Column('id', getter=lambda col,row: row.html.attrib.get('id')),
        Column('classes', getter=lambda col,row: row.html.attrib.get('class')),
    ]
    def iterload(self):
        from lxml import html
        utf8_parser = html.HTMLParser(encoding='utf-8')
        with self.source.open_text(encoding='utf-8') as fp:
            doc = html.parse(fp, parser=utf8_parser, base_url=self.source.given)
        self.setKeys([self.column('name')])
        self.column('keys').hide()
        self.column('source').hide()

        for i, e in enumerate(doc.iter('table')):
            if e.tag == 'table':
                yield HtmlTableSheet(e.attrib.get("id", "table_" + str(i)), source=e, html=e)

        yield HtmlLinksSheet(*self.names, 'links', source=doc, html=doc.getroot())


def is_header(elem):
    scope = elem.attrib.get('scope', '')

    if elem.tag == 'th':
        if not scope or scope == 'col':
            return True

    return False

class HtmlLinksSheet(Sheet):
    rowtype = 'links'  #  rowdef: tuple(element, attribute, link, pos)
    columns = [
        ItemColumn('element', 0, width=0),
        Column('tag', getter=lambda c,r:r[0].tag),
        ItemColumn('attribute', 1),
        Column('text', getter=lambda c,r:r[0].text),
        ItemColumn('link', 2, width=40),
    ]
    def iterload(self):
        from lxml.html import iterlinks
        root = self.source.getroot()
        root.make_links_absolute(self.source.docinfo.URL)
        yield from iterlinks(root)

    def openRow(self, row):
        return vd.openSource(row[2])

class HtmlElementsSheet(InferColumnsSheet):
    rowtype = 'links'  #  dict
    columns = [
        ItemColumn('__element__', width=0),
    ]
    def iterload(self):
        yield from self.source.iterlinks()
        return
        for r in self.source.iter(self.source_tag):
            row = copy.copy(r.attrib)
            row['__element__'] = r
            if row.get('href'):
                row['href'] = canonicalize_url(row.get('href'), self.source.URL)

            yield row

    def openRow(self, row):
        return vd.openSource(row.url)


class HtmlTableSheet(Sheet):
    rowtype = 'rows'  #  list of strings
    columns = []

    def iterload(self):
        headers = []

        maxlinks = {}  # [colnum] -> nlinks:int
        ncols = 0

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
                yield row
                ncols = max(ncols, colnum)

        self.columns = []
        if headers:
            it = itertools.zip_longest(*headers, fillvalue='')
        else:
            it = list(list(x) for x in self.rows.pop(0))
            it += [''] * (ncols-len(it))

        for colnum, names in enumerate(it):
            name = '_'.join(str(x) for x in names if x)
            self.addColumn(Column(name, getter=lambda c,r,i=colnum: r[i][0]))
            for linknum in range(maxlinks.get(colnum, 0)):
                self.addColumn(Column(name+'_link'+str(linknum), width=20, getter=lambda c,r,i=colnum,j=linknum: r[i][1][j]))


@VisiData.api
def save_html(vd, p, *vsheets):
    'Save vsheets as HTML tables in a single file'

    with open(p, 'w', encoding='ascii', errors='xmlcharrefreplace') as fp:
        for sheet in vsheets:

            if options.html_title:
                fp.write(options.html_title.format(sheet=sheet, vd=vd))

            fp.write('<table id="{sheetname}">\n'.format(sheetname=html.escape(sheet.name)))

            # headers
            fp.write('<tr>')
            for col in sheet.visibleCols:
                contents = html.escape(col.name)
                fp.write('<th>{colname}</th>'.format(colname=contents))
            fp.write('</tr>\n')

            # rows
            with Progress(gerund='saving'):
                for dispvals in sheet.iterdispvals(format=True):
                    fp.write('<tr>')
                    for val in dispvals.values():
                        fp.write('<td>')
                        fp.write(html.escape(val))
                        fp.write('</td>')
                    fp.write('</tr>\n')

            fp.write('</table>')
            vd.status('%s save finished' % p)


VisiData.save_htm = VisiData.save_html
