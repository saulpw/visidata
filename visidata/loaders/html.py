import html
import urllib.parse
import copy
import itertools
import re

from visidata import VisiData, vd, Sheet, options, Column, Progress, IndexSheet, ItemColumn

vd.option('html_title', '<h2>{sheet.name}</h2>', 'table header when saving to html')


@VisiData.api
def guess_html(vd, p):
    with p.open() as fp:
        r = fp.read(10240)
        if r.strip().startswith('<'):
            m = re.search(r, r'charset=(\S+)')
            if m:
                encoding = m.group(0)
            else:
                encoding = None
            return dict(filetype='html', _likelihood=1, encoding=encoding)

@VisiData.api
def open_html(vd, p):
    return HtmlTablesSheet(p.base_stem, source=p)

VisiData.open_htm = VisiData.open_html


class HtmlTablesSheet(IndexSheet):
    rowtype = 'sheets'  # rowdef: HtmlTableSheet (sheet.html = lxml.html.HtmlElement)
    columns = IndexSheet.columns + [
        Column('tag', width=0, getter=lambda col,row: row.html.tag),
        Column('id', getter=lambda col,row: row.html.attrib.get('id')),
        Column('classes', getter=lambda col,row: row.html.attrib.get('class')),
        Column('title', getter=lambda col,row: row.html.attrib.get('title')),
        Column('aria_label', getter=lambda col,row: row.html.attrib.get('aria-label')),
        Column('caption', getter=lambda col,row: row.html.xpath('normalize-space(./caption)') if row.html.xpath('./caption') else None, cache=True),
        Column('summary', getter=lambda col,row: row.html.attrib.get('summary')),
        Column('heading', getter=lambda col,row: row.html.xpath('normalize-space(./preceding-sibling::*[self::h1 or self::h2 or self::h3 or self::h4 or self::h5 or self::h6][1])') or None, cache=True),
    ]
    def iterload(self):
        lxml = vd.importExternal('lxml')
        from lxml import html
        with self.source.open(encoding='utf-8') as fp:
            doc = html.parse(fp, parser=vd.utf8_parser, base_url=self.source.given)
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
        lxml = vd.importExternal('lxml')
        from lxml.html import iterlinks
        root = self.source.getroot()
        root.make_links_absolute(self.source.docinfo.URL, handle_failures='ignore')
        yield from iterlinks(root)

    def openRow(self, row):
        return vd.openSource(row[2])

class HtmlElementsSheet(Sheet):
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
                row['href'] = urllib.parse.urljoin(self.source.URL, row.get('href'))

            yield row

    def openRow(self, row):
        return vd.openSource(row.url)


class HtmlTableSheet(Sheet):
    rowtype = 'rows'  #  list of strings
    columns = []

    def iterload(self):
        import lxml
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
                if isinstance(cell, lxml.etree.CommentBase):
                    continue
                cellval = ' '.join(x.strip() for x in cell.itertext())  # text only without markup
                links = [
                    vd.callNoExceptions(urllib.parse.urljoin, self.source.base_url, x.get('href')) or x.get('href')
                        for x in cell.iter('a')
                ]

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
                        row.append((None, []))
                    row[colnum] = (cellval, links)

                colnum += colspan

            if any(row):
                yield row
                ncols = max(ncols, colnum)

        self.columns = []
        if headers:
            it = itertools.zip_longest(*headers, fillvalue='')
        else:
            if len(self.rows) > 0:
                it = list(list(x) for x in self.rows.pop(0))
                it += [''] * (ncols-len(it))
            else:
                it = []

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


@VisiData.lazy_property
def utf8_parser(vd):
    lxml = vd.importExternal('lxml')
    return lxml.html.HTMLParser(encoding='utf-8')
#    return lxml.etree.HTMLParser(encoding='utf-8')


@VisiData.api
def HTML(vd, s):
    lxml = vd.importExternal('lxml')
    from lxml import html
    return html.fromstring(s, parser=vd.utf8_parser)


VisiData.save_htm = VisiData.save_html
