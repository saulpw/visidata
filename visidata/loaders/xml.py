from visidata import VisiData, vd, Sheet, options, Column, Progress, setitem, ColumnAttr, vlen, RowColorizer, Path, copy


@VisiData.api
def open_xml(vd, p):
    return XmlSheet(p.name, source=p)

VisiData.open_svg = VisiData.open_xml

def unns(k):
    'de-namespace key k'
    if '}' in k:
        return k[k.find('}')+1:]
    return k


def AttribColumn(name, k, **kwargs):
    return Column(name, getter=lambda c,r,k=k: r.attrib.get(k),
                        setter=lambda c,r,v,k=k: setitem(r.attrib, k, v), **kwargs)


# source is Path or xml.Element; root is xml.Element
class XmlSheet(Sheet):
    rowtype = 'elements'   # rowdef: lxml.xml.Element

    columns = [
        ColumnAttr('sourceline', type=int, width=0),
        ColumnAttr('prefix', width=0),
        ColumnAttr('nstag', 'tag', width=0),
        Column('path', width=0, getter=lambda c,r: c.sheet.root.getpath(r)),
        Column('tag', getter=lambda c,r: unns(r.tag)),
        Column('children', type=vlen, getter=lambda c,r: r.getchildren()),
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

    def iterload(self):
        if isinstance(self.source, Path):
            from lxml import etree, objectify
            self.root = etree.parse(self.source.open_text(encoding=self.options.encoding))
            objectify.deannotate(self.root, cleanup_namespaces=True)
        else: #        elif isinstance(self.source, XmlElement):
            self.root = self.source

        self.attribcols = {}
        self.columns = []
        for c in XmlSheet.columns:
            self.addColumn(copy(c))

        if getattr(self.root, 'iterancestors', None):
            for elem in Progress(list(self.root.iterancestors())[::-1]):
                yield elem

        for elem in self.root.iter():
            yield elem

    def openRow(self, row):
        return XmlSheet("%s_%s" % (unns(row.tag), row.attrib.get("id")), source=row)

    def addRow(self, elem):
        super().addRow(elem)
        for k in elem.attrib:
            if k not in self.attribcols:
                c = AttribColumn(unns(k), k)
                self.addColumn(c)
                self.attribcols[k] = c
                c.nstag = k


@VisiData.api
def save_xml(vd, p, vs):
    isinstance(vs, XmlSheet) or vd.fail('must save xml from XmlSheet')
    vs.root.write(str(p), encoding=options.encoding, standalone=False, pretty_print=True)


XmlSheet.addCommand('za', 'addcol-xmlattr', 'attr=input("add attribute: "); addColumnAtCursor(AttribColumn(attr, attr))', 'add column for xml attribute')
XmlSheet.addCommand('v', 'visibility', 'showColumnsBasedOnRow(cursorRow)', 'show only columns in current row attributes')
