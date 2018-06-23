from visidata import *

import re


def open_xml(p):
    from lxml import etree, objectify
    root=etree.parse(p.resolve())
    objectify.deannotate(root, cleanup_namespaces=True)
    return XmlSheet(p.name, source=root)
open_svg = open_xml


def unns(k):
    if '}' in k:
        return k[k.find('}')+1:]
    return k

class XmlSheet(Sheet):
    rowtype = 'elements'   # rowdef: lxml.xml.Element

    columns = [
        ColumnAttr('sourceline', type=int, width=0),
        ColumnAttr('prefix', width=0),
        ColumnAttr('nstag', 'tag', width=0),
        Column('tag', getter=lambda c,r: unns(r.tag)),
        Column('children', type=len, getter=lambda c,r: r.getchildren()),
        ColumnAttr('text'),
        ColumnAttr('tail', width=0),
    ]

    commands = [
        Command('v', 'showColumnsBasedOnRow(cursorRow)', 'show only columns in current row attributes', ),
        Command(ENTER, 'r=cursorRow; vd.push(XmlSheet("%s_%s" % (unns(r.tag), r.attrib.get("id")), source=r))', 'dive into this element')
    ]

    def showColumnsBasedOnRow(self, row):
        for c in self.columns:
            nstag = getattr(c, 'nstag', '')
            if nstag:
                c.hide(nstag not in row.attrib)

    def reload(self):
        self.attribcols = {}
        self.columns = copy(XmlSheet.columns)
        self.rows = []

        for elem in self.source.iter():
            self.addRow(elem)

    def addRow(self, elem):
        self.rows.append(elem)
        for k in elem.attrib:
            if k not in self.attribcols:
                c = Column(unns(k), getter=lambda c,r,k=k: r.attrib.get(k),
                                    setter=lambda c,r,v,k=k: setitem(r.attrib, k, v))
                self.addColumn(c)
                self.attribcols[k] = c
                c.nstag = k
