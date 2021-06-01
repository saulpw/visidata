#!/usr/bin/env python3

__all__=[ 'SelectorColumn', 'soupstr' ]

from visidata import *

import os.path
from urllib.parse import urljoin

import concurrent.futures

@VisiData.api
def soup(vd, s):
    from bs4 import BeautifulSoup
    return BeautifulSoup(s, 'html.parser')

@VisiData.api
def enable_requests_cache(vd):
    try:
        import requests
        import requests_cache

        requests_cache.install_cache(str(Path(os.path.join(options.visidata_dir, 'httpcache'))), backend='sqlite', expire_after=24*60*60)
    except ModuleNotFoundError:
        vd.warning('install requests_cache for less intrusive scraping')


@VisiData.api
def open_scrape(vd, p):
    vd.enable_requests_cache()
    if p.is_url():
        return HtmlDocsSheet(p.name, source=p, urls=[p.given])
    else:
        return HtmlElementsSheet(p.name, source=p, elements=None)

def node_name(node):
    me = node.name
    class_ = node.attrs.get("class")
    if class_:
        me += '.' + class_[0]
    id_ = node.attrs.get("id")
    if id_:
        me += '#' + id_
    return me

@functools.lru_cache(maxsize=None)
def calc_selector(node):
    if not node.parent:
        return ''

    psel = calc_selector(node.parent)
    oursel = node_name(node)
    if not psel:
        return oursel

    root = list(node.parents)[-1]

    combinedsel = psel+' '+oursel
    if len(root.select(combinedsel)) == len(root.select(oursel)):
        return oursel

    return combinedsel


class HtmlAttrColumn(Column):
    def calcValue(self, row):
        return row.attrs.get(self.expr)

def _getRootSheet(sheet):
    if not isinstance(sheet.source, Sheet):
        return sheet
    return _getRootSheet(sheet.source)

def prev_header(r):
    hdrtags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    try:
        i = hdrtags.index(r.name)
        return r.find_previous(hdrtags[:i-1])
    except Exception:
        return r.find_previous(hdrtags)


# one row per element
class HtmlElementsSheet(Sheet):
    # source=[element, ...]
    rowtype='dom nodes'  # rowdef soup.element
    columns = [
        Column('name', getter=lambda c,r: node_name(r)),
        Column('selector', getter=lambda c,r: calc_selector(r), cache='async', width=0),
        AttrColumn('string'),
        Column('depth', cache=True, getter=lambda c,r: list(c.sheet.parents(r))),
        Column('prev_header', getter=lambda c,r: prev_header(r), cache=True),
        HtmlAttrColumn('href', expr='href'),
    ]
    def iterload(self):
        for el in self.elements or [vd.soup(self.source.read_text())]:
            for x in el.find_all():
                if x.string:
                    yield x

    def parents(self, row):
        while row.parent and row.parent is not row:
            yield row.parent
            row = row.parent

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
        return [x.string for x in row.soup.select(self.expr)]


class HtmlDocsSheet(Sheet):
    rowtype='requests'  # rowdef: requests.Response
    columns = [
        AttrColumn('url'),
        AttrColumn('status_code', type=int),
        AttrColumn('from_cache'),
        AttrColumn('fetched_at', 'created_at', type=date, width=0),
        AttrColumn('expires', type=date),
        AttrColumn('reason'),
        AttrColumn('soup.title.string'),
    ]
    def iterload(self):
        import requests
        self.colnames = {}
#        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
#            yield from executor.map(requests.get, Progress(self.urls))
        for url in Progress(self.urls):
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
HtmlDocsSheet.addCommand(';', 'addcol-selector', 'sel=input("css selector: ", type="selector"); addColumn(SelectorColumn(sel, expr=sel, cache="async"))')

vd.addGlobals({'SelectorColumn':SelectorColumn,
                        'soupstr':soupstr})
