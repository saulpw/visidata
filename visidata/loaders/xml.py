from visidata import *

def open_xml(p):
    from lxml import etree, objectify
    root = etree.parse(p.open_text())
    objectify.deannotate(root, cleanup_namespaces=True)
    return XmlSheet(p.name, source=root)
open_svg = open_xml


@asyncthread
def save_xml(p, vs):
    vs.source.write(p.resolve(), encoding=options.encoding, standalone=False, pretty_print=True)
save_svg = save_xml


def unns(k):
    if '}' in k:
        return k[k.find('}')+1:]
    return k


def AttribColumn(name, k, **kwargs):
    return Column(name, getter=lambda c,r,k=k: r.attrib.get(k),
                        setter=lambda c,r,v,k=k: setitem(r.attrib, k, v), **kwargs)


class XmlSheet(Sheet):
    rowtype = 'elements'   # rowdef: lxml.xml.Element

    columns = [
        ColumnAttr('sourceline', type=int, width=0),
        ColumnAttr('prefix', width=0),
        ColumnAttr('nstag', 'tag', width=0),
        Column('path', width=0, getter=lambda c,r: c.sheet.source.getpath(r)),
        Column('tag', getter=lambda c,r: unns(r.tag)),
        Column('children', type=len, getter=lambda c,r: r.getchildren()),
        ColumnAttr('text'),
        ColumnAttr('tail', width=0),
    ]
    colorizers = [
            RowColorizer(8, None, lambda s,c,r,v: 'green' if r is s.source else None)
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

        if getattr(self.source, 'iterancestors', None):
            for elem in list(self.source.iterancestors())[::-1]:
                self.addRow(elem)

        for elem in self.source.iter():
            self.addRow(elem)

    def addRow(self, elem):
        self.rows.append(elem)
        for k in elem.attrib:
            if k not in self.attribcols:
                c = AttribColumn(unns(k), k)
                self.addColumn(c)
                self.attribcols[k] = c
                c.nstag = k

XmlSheet.addCommand('za', 'add-column', 'attr=input("add attribute: "); addColumn(AttribColumn(attr, attr), cursorColIndex+1)')
XmlSheet.addCommand('v', 'visibility', 'showColumnsBasedOnRow(cursorRow)')
XmlSheet.addCommand(ENTER, 'dive-row', 'r=cursorRow; vd.push(XmlSheet("%s_%s" % (unns(r.tag), r.attrib.get("id")), source=r))')

