#!/usr/bin/env python3

from visidata import *


@VisiData.api
def soup(vd, s):
    from bs4 import BeautifulSoup
    return BeautifulSoup(s, 'html.parser')


@VisiData.api
def open_scrape(vd, p):
    return HtmlLinksSheet(p.name, source=p)


def genSelector(c, node):
    me = ' ' + node.name
    class_ = node.attrs.get("class")
    if class_:
        me += '.' + class_[0]
    id_ = node.attrs.get("id")
    if id_:
        me += '#' + id_[0]
    if node.parent:
        return genSelector(c, node.parent) + me
    else:
        return me

class HrefColumn(Column):
    def calcValue(self, row):
        return r.attrs['href']

class HtmlLinksSheet(Sheet):
    rowtype='dom nodes'
    columns = [
            Column('selector', getter=genSelector),
            ColumnAttr('text'),
            Column('href', getter=lambda c,r: r.attrs['href']),
    ]
    @asyncthread
    def reload(self):
        self.soup = vd.soup(self.source.open_text())
        self.rows = []
        for link in self.soup.find_all():
            self.addRow(link)

    def openRow(self, row):
        return open_scrape(Path(row.attrs["href"]))


class HtmlDiffSheet(Sheet):
    rowtype='dom nodes'
    columns = [
            Column('selector', getter=genSelector),
            ColumnAttr('text'),
            Column('href', getter=lambda c,r: r.attrs['href']),
    ]
    @asyncthread
    def reload(self):
        self.soup = vd.soup(self.source.open_text())
        self.rows = []
        for link in self.soup.find_all():
            self.addRow(link)


