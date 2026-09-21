from copy import copy
from visidata import VisiData, vd, Sheet, options, Column, Progress, setitem, ColumnAttr, vlen, RowColorizer, Path

vd.option('xml_parser_huge_tree', True, 'allow very deep trees and very long text content')
vd.option('xml_parser_recover', True, 'try hard to parse through broken XML')


@VisiData.api
def open_xml(vd, p):
    return XmlSheet(p.base_stem, source=p)

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
            vd.importExternal('lxml')
            from lxml import etree, objectify
            p = etree.XMLParser(**self.options.getall('xml_parser_'))
            with self.open_text_source() as fp:
                self.root = etree.parse(fp, parser=p)
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


def xml_text(elem):
    text = ''.join(elem.xpath('text()'))
    return text if text.strip() else ''


def xml_single(values):
    if len(values) == 1:
        return values[0]
    return values or None


def xml_value(elem):
    children = list(elem.iterchildren(tag='*'))
    text = xml_text(elem)
    if not elem.attrib and not children:
        return text

    record = {unns(k): v for k, v in elem.attrib.items()}
    if text:
        record['_text'] = text
    groups = {}
    for child in children:
        groups.setdefault(unns(child.tag), []).append(xml_value(child))
    record.update((k, xml_single(v)) for k, v in groups.items())
    return record


def xml_project(value, func):
    'Apply a projection while retaining nested lists and missing positions.'
    if isinstance(value, list):
        return [xml_project(item, func) for item in value]
    if value is not None:
        return func(value)


def xml_elements(value):
    if isinstance(value, list):
        for item in value:
            yield from xml_elements(item)
    elif value is not None:
        yield value


class XmlSchema:
    def __init__(self):
        self.fields = {}
        self.children = {}
        self.record = False

    def observe(self, elem, changed=None):
        if changed is None:
            changed = set()
        before = self.record, len(self.fields)
        children = list(elem.iterchildren(tag='*'))
        self.record |= bool(elem.attrib or children)
        for key, value in elem.attrib.items():
            if value.strip():
                self.fields.setdefault(('attr', key), None)
        if xml_text(elem):
            self.fields.setdefault(('text', '_text'), None)
        for child in children:
            if child.tag not in self.children:
                self.children[child.tag] = XmlSchema()
            schema = self.children[child.tag]
            schema.observe(child, changed)
            if schema.fields:
                self.fields.setdefault(('child', child.tag), schema)
        if before != (self.record, len(self.fields)):
            changed.add(self)
        return changed


class XmlColumn(Column):
    def __init__(self, field, schema, parent=None):
        kind, key = field
        name = unns(key)
        if parent is not None:
            name = parent.sheet.options.fmt_expand_dict % (parent.name, name)
        super().__init__(name, expr=key, xml_kind=kind, xml_schema=schema)
        self.xml_columns = None
        if parent is not None:
            self.origCol = parent
        elif kind == 'attr':
            self.setter = lambda c,r,v: setitem(r.attrib, c.expr, v)

    def elements(self, row):
        parent = getattr(self, 'origCol', None)
        value = parent.elements(row) if parent is not None else row
        if self.xml_kind == 'child':
            return xml_project(value, lambda elem: xml_single([
                child for child in elem if child.tag == self.expr]))
        return value

    def calcValue(self, row):
        value = self.elements(row)
        if self.xml_kind == 'attr':
            return xml_project(value, lambda elem: elem.attrib.get(self.expr))
        if self.xml_kind == 'text':
            return xml_project(value, lambda elem: xml_text(elem) or None)
        return xml_project(value, xml_value)

    def expand(self, rows):
        if self.xml_kind != 'child':
            return []
        self.xml_columns = {f: c for f,c in (self.xml_columns or {}).items() if c in self.sheet.columns}
        if not self.xml_schema.record:
            return []
        index = self.sheet.columns.index(self) + 1
        for i, existing in enumerate(self.sheet.columns):
            parent = getattr(existing, 'origCol', None)
            while parent is not None and parent is not self:
                parent = getattr(parent, 'origCol', None)
            if parent is self:
                index = max(index, i + 1)
        for field, schema in self.xml_schema.fields.items():
            if field not in self.xml_columns:
                col = XmlColumn(field, schema, parent=self)
                self.sheet.addColumn(col, index=index)
                self.xml_columns[field] = col
                index += 1
        if self.xml_columns:
            self.hide()
        return list(self.xml_columns.values())


# rowdef: lxml element shared with the source XML tree
class XmlTableSheet(Sheet):
    rowtype = 'elements'

    def iterload(self):
        self.columns = []
        self.xml_schema = XmlSchema()
        self.xml_fields = set()
        self.xml_tags = set()
        for elem in Progress(self.source, total=0):
            if isinstance(elem.tag, str):
                yield elem

    def addRow(self, elem, index=None):
        ret = super().addRow(elem, index=index)
        self.xml_tags.add(elem.tag)
        if len(self.xml_tags) == 2 and not any(c.name == '_tag' for c in self.columns):
            self.addColumn(Column('_tag', getter=lambda c,r: unns(r.tag)))
        changed = self.xml_schema.observe(elem)
        if self.xml_schema in changed:
            for field, schema in self.xml_schema.fields.items():
                if field not in self.xml_fields:
                    self.addColumn(XmlColumn(field, schema))
                    self.xml_fields.add(field)
        if changed:
            for col in list(self.columns):
                if isinstance(col, XmlColumn) and col.xml_schema in changed and col.xml_columns is not None:
                    if not col.xml_columns or any(c in self.columns for c in col.xml_columns.values()):
                        col.expand(None)
        return ret

    def openRow(self, row):
        return XmlTableSheet(self.name, unns(row.tag), source=row)

    def openCell(self, col, row, rowidx=None):
        if isinstance(col, XmlColumn) and col.xml_kind == 'child':
            return XmlTableSheet(self.name, col.name, source=xml_elements(col.elements(row)))
        return super().openCell(col, row, rowidx)


@VisiData.api
def save_xml(vd, p, vs):
    isinstance(vs, XmlSheet) or vd.fail('must save xml from XmlSheet')
    vs.root.write(str(p), encoding=vs.options.save_encoding, standalone=False, pretty_print=True)

XmlSheet.options.save_encoding = 'utf-8'  #2520

XmlSheet.addCommand('za', 'addcol-xmlattr', 'attr=input("add attribute: "); addColumnAtCursor(AttribColumn(attr, attr))', 'add column for xml attribute')
XmlSheet.addCommand('v', 'visibility', 'showColumnsBasedOnRow(cursorRow)', 'show only columns in current row attributes')
XmlSheet.addCommand('', 'dive-xml-table', 'vd.push(XmlTableSheet(name, unns(cursorRow.tag), source=cursorRow))', 'open immediate children of current XML element as a table')

vd.addGlobals(XmlTableSheet=XmlTableSheet, unns=unns)

vd.addMenuItems('''
    Data > Dive > XML table > dive-xml-table
''')
