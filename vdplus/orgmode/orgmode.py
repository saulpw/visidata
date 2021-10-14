import collections
import datetime

from visidata import *
import orgparse


@VisiData.api
def open_forg(vd, p):
    return OrgSheet(p.name, source=p)


class OrgRows(list):
    def __init__(self, *args, sheet=None):
        super().__init__(*args)
        self._sheet = sheet

    # inputLongname
    def _deepiter(self, objlist):
        for obj in objlist:
            yield obj
            if self._sheet and id(obj) in self._sheet.opened_rows:
                yield from self._deepiter(obj.children)

    @property
    def _actual_list(self):
        return list(self._deepiter(self))

    def __len__(self):
        return len(self._actual_list)

    def __getitem__(self, k):
        if isinstance(k, slice):
            return OrgRows(self._actual_list[k], sheet=self._sheet)

        return self._actual_list[k]


class ArbitraryDictSheet(Sheet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._knownKeys = set()  # set of row keys already seen

    @asyncthread
    def reload(self):
        self.rows = []
        self.columns = []
        self._knownKeys.clear()
        for c in type(self).columns:
            self.addColumn(deepcopy(c))
            self._knownKeys.add(c.expr)

        try:
            with vd.Progress(gerund='loading', total=0):
                for r in self.iterload():
                    self.addRow(r)
        except FileNotFoundError:
            return  # let it be a blank sheet without error

        # if an ordering has been specified, sort the sheet
        if self._ordering:
            vd.sync(self.sort())

    def addRow(self, row, index=None):
        super().addRow(row, index=index)

        for k in row:
            if k not in self._knownKeys:
                self.addColumn(ColumnItem(k, type=deduceType(row[k])))
                self._knownKeys.add(k)
        return row

def encode_date(dt=None):
    if not dt:
        dt = datetime.datetime.now()
    elif isinstance(dt, str):
        dt = datetime.datetime.fromisoformat(dt)

    s = '123456789abcdefghijklmnopqrstuvwxyz'
    return '%02d%s%s' % (dt.year % 100, s[dt.month-1], s[dt.day-1])


class OrgContentsColumn(Column):
    def setValue(self, row, v):
        super().setValue(row, v)
        orgmode_parse_into(_root(row), v)

    def putValue(self, row, v):
        self.sheet.save(row)


def orgmode_parse_into(toprow, fullfile, **kwargs):
    toprow.update(kwargs)

    lines = fullfile.splitlines()
    top_section = section = toprow # AttrDict(contents='', tags=[], level=0, children=[])
#    toprow.children = [section]
    for linenum, line in enumerate(lines):
        section.tags.extend(re.findall(r':\S+?:', line))
        g = orgmode_parse_title(line)
        if g:
            assert top_section or section in section.parent.children
            parent = section
            section = OrgSheet().newRow()
            section.update(g)
            section.linenum = linenum


            while parent and section.level < parent.level:
                parent = parent.parent

            if not parent:
                toprow.children.append(section)
                continue


            if section.level > parent.level:
                parent.children.append(section)
                section.parent = parent
                continue
            elif section.level == parent.level:
                if parent.parent:
                    parent.parent.children.append(section)
                    section.parent = parent.parent
                else:
                    toprow.children.append(parent)
        else:
            # m = re.search(r'^#+BEGIN_(?P<name>\S+)\s*(?P<parms>.*)', line)
            section.contents += line + '\n'

    if not toprow.title and len(toprow.children) == 1:
        real = toprow.children[0]
        toprow.title = real.title

#    if top_section and top_section.contents:
#        toprow.children.insert(0, top_section)


def orgmode_to_string(section, prestars=''):
    ret = ''
    if section.title:
        ret += prestars[len(section.stars):] + (section.title or ' ') + '\n'
    ret += section.contents or ''
    ret += ''.join(orgmode_to_string(c, prestars+(section.stars or '')) for c in section.children)
    return ret


def orgmode_parse_title(line):
    m = re.search(r'^(?P<stars>[*#]+)\s+(?P<keyword>(TODO|FEEDBACK|VERIFY|DONE|DELEGATED))?\s*(?P<prio>\[#[A-z]\])?\s*(?P<title>.*)', line)
    if m:
        return dict(stars=m.group('stars'),
                    level=len(m.group('stars')),
                    keyword=m.group('keyword') or '',
                    prio=m.group('prio') or '',
                    title=line)
    else:
        return {}

class OrgSheet(Sheet):
    defer = True
    columns = [
        Column('id', width=15, getter=lambda c,r: r.path.stem, setter=lambda c,r,v: setattr(r, 'path', r.path.rename(r.path.with_stem(v)))),
        ItemColumn('path', width=0),
        ItemColumn('date', width=0, type=date),
        ItemColumn('title', width=40),
        ItemColumn('contents', width=0),
        Column('tags', width=10, getter=lambda c,r: ' '.join(r.tags)),
        ItemColumn('children'),
#       Column('linenum', type=int, getter=lambda c,r: r.linenum),
        Column('to_string', width=0, getter=lambda c,r: orgmode_to_string(r)),
        OrgContentsColumn('file_string', width=0, getter=lambda c,r: r.file_string),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opened_rows = set()
#        self.open_max=0  # all levels closed after this point
#        self.close_max=0 # all levels open after this point

    @property
    def rows(self):
        return self._rows

    @rows.setter
    def rows(self, v):
        if v is not UNLOADED:
            v = OrgRows(v, sheet=self)
        self._rows = v

    def openRows(self, rows):
        for row in rows:
            self.opened_rows.add(id(row))

    def closeRows(self, rows=None):
        if rows is None:
            for row in rows:
                self.opened_rows.remove(id(row))
        else:
            self.opened_rows.clear()

    def newRow(self):
        return AttrDict(contents='', tags=[], children=[], level=0)

    def iterload(self):
        self.rows = []
        for fn in self.source.open_text():
            p = Path(fn.rstrip())

            row = self.newRow()
            row.path = p
            row.tags = []
            st = p.stat()
            if st:
                row.date = st.st_mtime

            row.file_string = p.read_text()
            orgmode_parse_into(row, row.file_string, path=p)
            yield row

    def draw(self, scr):
        super().draw(scr)

    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()

        for row in adds.values():
            self.save(row)

        self.commitAdds()

        self.commitMods()

        for row in dels.values():
            row.path.rename('%s-%s' % (row.path, encode_date()))

        self.commitDeletes()

    def save(self, row):
        try:
            row.path.rename('%s-%s' % (row.path, encode_date()))  # backup
        except FileNotFoundError:
            pass

        with row.path.open(mode='w') as f:
            print(orgmode_to_string(row), file=f, end='')


@OrgSheet.api
def paste_into(sheet, row, sourcerows, cols):
    body = row.body or ''
    for r in sourcerows:
        data = vd.encode_json(r, cols)
        body += f':{cols[0].sheet.name}:{data}\n'
    sheet.column('body').setValue(row, body)


@OrgSheet.api
def combine_rows(sheet, rows):
    newrow = sheet.newRow()
    newrow.date = datetime.datetime.today()
    orgid = clean_to_id(rows[0].title)
    newrow.path = Path('~/lifefs/zk')/((orgid or encode_date())+'.org')
    for r in rows:
        hdr = sheet.newRow()
        if hdr.title:
            g = orgmode_parse_title(hdr.title)
            hdr.update(g)
        hdr.children = list(r.children)
        newrow.children.append(hdr)
#    newrow.title = ' '
    newrow.file_string = orgmode_to_string(newrow, '*')
    return newrow


def _root(row):
    while row.parent:
        row = row.parent
    return row


@OrgSheet.api
def sysopen_row(sheet, row):
    root = _root(row)
    if root.path.exists():
        vd.launchEditor(root.path)
    else:
        orgmode_parse_into(row, vd.launchExternalEditor(root.file_string))


OrgSheet.addCommand('^O', 'sysopen-row', 'sysopen_row(cursorRow)', 'open current file in external $EDITOR')
OrgSheet.addCommand('g^O', 'sysopen-rows', 'launchEditor(*(r.path for r in selectedRows))', 'open selected files in external $EDITOR')
OrgSheet.addCommand('^J', 'expand-row', 'openRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('z^J', 'close-row', 'closeRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('g^J', 'expand-selected', 'openRows(selectedRows)')
OrgSheet.addCommand('gz^J', 'close-selected', 'closeRows(selectedRows)')
OrgSheet.addCommand('ga', 'combine-selected', 'addRows([combine_rows(selectedRows)], index=cursorRowIndex); cursorDown(1)', 'combine selected rows into new org entry')

OrgSheet.addCommand('p', 'paste-rows', 'paste_into(cursorRow, vd.memory.cliprows, vd.memory.clipcols)', 'append clipboard rows to current zk')


if __name__ == '__main__':
    for fn in sys.argv[1:]:
        sect = OrgSheet().newRow()
        sect.file_string = Path(fn).read_text()
        orgmode_parse_into(sect, sect.file_string, path=Path(fn))
        print(orgmode_to_string(sect), end='')
