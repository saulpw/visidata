#!/usr/bin/env python3

__all__=[ 'SelectorColumn', 'soupstr' ]

from visidata import *

import os.path
from urllib.parse import urljoin

try:
    import requests
    import requests_cache

    requests_cache.install_cache(str(Path(os.path.join(options.visidata_dir, 'httpcache'))), backend='sqlite', expire_after=24*60*60)
except ModuleNotFoundError:
    pass


@VisiData.api
def soup(vd, s):
    from bs4 import BeautifulSoup
    return BeautifulSoup(s, 'html.parser')


@VisiData.api
def open_scrape(vd, p):
    if p.is_url():
        return HtmlDocsSheet(p.name, source=p, urls=[p.given])
    else:
        return HtmlElementsSheet(p.name, source=p, elements=[vd.soup(p.read_text())])

def node_name(node):
    me = ' ' + node.name
    class_ = node.attrs.get("class")
    if class_:
        me += '.' + class_[0]
    id_ = node.attrs.get("id")
    if id_:
        me += '#' + id_[0]
    return me

def calc_selector(node):
    if node.parent:
        return calc_selector(node.parent) + node_name(node)
    else:
        return ''


class HtmlAttrColumn(Column):
    def calcValue(self, row):
        return row.attrs[self.expr]

def _getRootSheet(sheet):
    if not isinstance(sheet.source, Sheet):
        return sheet
    return _getRootSheet(sheet.source)


# one row per element
class HtmlElementsSheet(Sheet):
    # source=[element, ...]
    rowtype='dom nodes'  # rowdef soup.element
    columns = [
        Column('name', getter=lambda c,r: node_name(r)),
        Column('selector', getter=lambda c,r: calc_selector(r)),
        AttrColumn('text'),
        HtmlAttrColumn('href', expr='href'),
    ]
    def iterload(self):
        for el in self.elements:
            yield from el.find_all()

    @property
    def rootSource(self):
        return _getRootSheet(self).source

    def openRows(self, rows):
        realurls = [urljoin(self.rootSource.given, r.attrs.get('href')) for r in rows]
        yield HtmlDocsSheet(self.name, 'scrape', source=self, urls=realurls)

    def openRow(self, row):
        'opening a single row'
        return HtmlElementsSheet('', source=self, elements=[row])


class SelectorColumn(Column):
    def calcValue(self, row):
        return row.soup.select(self.expr)


class HtmlDocsSheet(Sheet):
    rowtype='requests'  # rowdef: requests.Response
    columns = [
        AttrColumn('url'),
        AttrColumn('status_code'),
        AttrColumn('reason'),
        AttrColumn('soup.title'),
    ]
    def iterload(self):
        import requests
        self.colnames = {}
        for url in self.urls:
            yield requests.get(url)

    def addRow(self, row, index=None):
        super().addRow(row, index=index)
        try:
            row.soup = vd.soup(row.text)
        except Exception:
            row.soup = None

    def openRow(self, row):
        return HtmlElementsSheet(row.url, source=self, elements=[row.soup])

def soupstr(coll):
    return ' '.join(v.string for v in coll)

vdtype(soupstr, 's')

HtmlElementsSheet.addCommand('~', 'type-soupstr', 'cursorCol.type=soupstr')
HtmlElementsSheet.addCommand('go', 'open-rows', 'for vs in openRows(selectedRows): vd.push(vs)')
HtmlDocsSheet.addCommand(';', 'addcol-selector', 'sel=input("css selector: ", type="selector"); addColumn(SelectorColumn(sel, expr=sel))')
