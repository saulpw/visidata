import collections
import datetime
import re

from visidata import *
import orgparse


@VisiData.api
def open_org(vd, p):
    return OrgSheet(p.name, source=p, filetype='org')


@VisiData.api
def open_forg(vd, p):
    return OrgSheet(p.name, source=p, filetype='forg')


@VisiData.api
def open_orgdir(vd, p):
    return OrgSheet(p.name, source=p, filetype='orgdir')


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


def sectionize(lines):
    'Generate (startinglinenum, contentlines) for each section.  First section may not have leading * or # but all others will.'
    startinglinenum = 0
    contents = []
    for linenum, line in enumerate(lines):
        line = line.strip()
        if not line and not contents:
            continue  # ignore leading blank lines

        if line and line[0] in '#*':
            if contents:
                yield startinglinenum, contents
                contents = []
                startinglinenum = linenum

        contents.append(line)

    if contents:
        yield startinglinenum, contents


def orgmode_parse(all_lines):
    root = parent = OrgSheet().newRow()
    for linenum, lines in sectionize(all_lines):
        section = OrgSheet().newRow()
        section.contents = '\n'.join(lines)
        for line in lines:
            section.tags.extend(re.findall(r':([\S:]+?):', line))
            links = re.findall(r'\[.*?\]\(.*?\)', line)
            if links:
                section.links.extend(links)

        title = orgmode_parse_title(lines[0])
        if not title:
            assert lines[0][0] not in '#*', (linenum, lines)
            root = parent = section
            continue

        section.update(title)
        section.linenum = linenum+1

        while parent and section.level <= parent.level:
            parent = parent.parent

        parent.children.append(section)
        section.parent = parent
        parent = section

    return root


def orgmode_parse_into(toprow, fullfile, **kwargs):
    row = orgmode_parse(fullfile.splitlines())
    toprow.update(row)
    toprow.update(kwargs)


def orgmode_to_string(section, prestars=''):
    ret = ''

#    if section.title:
#        ret += prestars[len(section.stars):] + (section.title or ' ') + '\n'
    ret += section.contents or ''
    ret += ''.join(orgmode_to_string(c, prestars+(section.stars or '')) for c in section.children)
    return ret


def orgmode_parse_title(line):
    m = re.match(r'^(?P<stars>[*#]+)\s*(?P<keyword>(TODO|FEEDBACK|VERIFY|DONE|DELEGATED))?\s*(?P<prio>\[#[A-z]\])?\s*(?P<title>.*)', line)
    if not m:
        assert not line or line[0] not in '#*', line
        return {}

    return dict(stars=m.group('stars'),
                level=len(m.group('stars')),
                keyword=m.group('keyword') or '',
                prio=m.group('prio') or '',
                title=line)

class OrgSheet(Sheet):
    defer = True
    columns = [
        Column('path', getter=lambda c,r: _root(r).path, width=0),
        Column('id', width=0, getter=lambda c,r: _root(r).path.stem),
        ItemColumn('title', width=40),
        ItemColumn('date', width=0, type=date),
        ItemColumn('tags', width=10, type=lambda v: ' '.join(v)),
        ItemColumn('links', type=vlen),
        ItemColumn('parent', width=0),
        ItemColumn('children', type=vlen),
        ItemColumn('linenum', width=0, type=int),
        Column('to_string', width=0, getter=lambda c,r: orgmode_to_string(r)),
        OrgContentsColumn('file_string', width=0, getter=lambda c,r: r.file_string),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.opened_rows = set()
#        self.open_max=0  # all levels closed after this point
#        self.close_max=0 # all levels open after this point

    def isSelectedParents(self, row):
        return super().isSelected(row) or row.parent and self.isSelectedParents(row.parent)

    def isSelected(self, row):
        return self.isSelectedParents(row)

    def refreshRows(self):
        self.rows = list(self._deepiter(self.sourceRows))

    def _deepiter(self, objlist, depth=1):
        for obj in objlist:
            if not obj.parent and obj.children:
                # ignore toplevel file, dive into subrows
                yield from self._deepiter(obj.children, depth)
            else:
                yield obj
                if id(obj) in self.opened_rows:
                    yield from self._deepiter(obj.children, depth-1)

    def openRows(self, rows):
        for row in rows:
            self.opened_rows.add(id(row))
        self.refreshRows()

    def closeRows(self, rows=None):
        if rows is None:
            for row in rows:
                self.opened_rows.remove(id(row))
        else:
            self.opened_rows.clear()
        self.refreshRows()

    def newRow(self):
        return AttrDict(contents='', tags=[], children=[], links=[], level=0, linenum=0)

    def iterload(self):
        self.rows = []
        def _walkfiles(p):
            basepath = str(p)
            for folder, subdirs, files in os.walk(basepath):
                subfolder = folder[len(basepath)+1:]
                if subfolder.startswith('.'): continue
                if subfolder in ['.', '..']: continue

                fpath = Path(folder)
                yield fpath

                for fn in files:
                    yield fpath/fn

        if self.filetype == 'orgdir':
            basepath = str(self.source)
            for p in _walkfiles(self.source):
                if p.name.startswith('.'): continue
                if p.ext in ['org', 'md']:
                    yield self.parse_orgmd(p)
        elif self.filetype == 'forg':
            for fn in self.source.open_text():
                yield self.parse_orgmd(Path(fn.rstrip()))
        elif self.filetype == 'org':
            yield self.parse_orgmd(self.source)

        self.sourceRows = self.rows
        self.refreshRows()

    def parse_orgmd(self, path):
#        row.file_string = open(path).read()
        vd.debug(path)
        row = orgmode_parse(open(path).readlines())
        row.path = path
        st = path.stat()
        if st:
            row.date = st.st_mtime

        return row

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
            hdr.update(orgmode_parse_title(hdr.title))
        hdr.children = list(r.children)
        newrow.children.append(hdr)
#    newrow.title = ' '
    newrow.file_string = orgmode_to_string(newrow, '*')
    return newrow


def _root(row):
    while row and row.parent:
        row = row.parent
    return row


@OrgSheet.api
def sysopen_row(sheet, row):
    root = _root(row)
    if root.path.exists():
        vd.launchEditor(root.path, '+%s'%row['linenum'])
    else:
        orgmode_parse_into(row, vd.launchExternalEditor(root.file_string))

@VisiData.api
def save_org(vd, p, *vsheets):
    with p.open_text(mode='w', encoding=vsheets[0].options.encoding) as fp:
        for vs in vsheets:
            if isinstance(vs, OrgSheet):
                for row in vs.rows:
                    print(orgmode_to_string(row).strip(), file=fp)
            else:
                vd.warning('not implemented')



@OrgSheet.api
def sysopen_rows(sheet, rows):
    ret = ''
    for r in rows:
        s = orgmode_to_string(r).strip()
        ret += '{::%s::}\n%s\n\n' % (id(r), s)

    ret = vd.launchExternalEditor(ret + "{::}")

    idrows = {id(r):r for r in rows}
    for idtag, text in re.findall(r'\{::(\d+)::\}(.*?)\{::', ret, re.DOTALL):
        idtag = int(idtag)
        row = idrows.get(idtag, None)
        if not row:
            vd.warning('no id(%s), adding in current section' % idtag)
            row = sheet.newRow()
            sheet.addRow(row)

        vd.status(idtag, text)
        orgmode_parse_into(row, text.strip())


OrgSheet.addCommand('^O', 'sysopen-row', 'sysopen_row(cursorRow)', 'open current file in external $EDITOR')
OrgSheet.addCommand('g^O', 'sysopen-rows', 'sysopen_rows(selectedRows)', 'open selected files in external $EDITOR')
OrgSheet.addCommand('^J', 'expand-row', 'openRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('z^J', 'close-row', 'closeRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('g^J', 'expand-selected', 'openRows(selectedRows)')
OrgSheet.addCommand('gz^J', 'close-selected', 'closeRows(selectedRows)')
OrgSheet.addCommand('ga', 'combine-selected', 'addRows([combine_rows(selectedRows)], index=cursorRowIndex); cursorDown(1)', 'combine selected rows into new org entry')

OrgSheet.addCommand('p', 'paste-rows', 'paste_into(cursorRow, vd.memory.cliprows, vd.memory.clipcols)', 'append clipboard rows to current zk')


if __name__ == '__main__':
    for fn in sys.argv[1:]:
        sect = orgmode_parse_into(Path(fn))
        print(orgmode_to_string(sect).strip())
