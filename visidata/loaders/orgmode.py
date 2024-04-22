'''
View sections in one or more .org files.  Easily edit sections within the system editor.

## Supported syntax

- `--- [comment]` at start of line starts a new section
- any number of `#` or `*` (followed by a space) leads a headline
- `#+key: value` adds metadata to next element (headline, table, section, )
- orgmode style tags: `:tag1:tag2:`
- `[[tagname]]` links to that set of tags
- `[[url]]` links to external url
- orgmode and markdown links
   - `[[url][linktext]]`
   - `[linktext](url)`
- all other markup/orgmode/whatever is ignored and passed through

## Usage

- `vd file.org`
- or `find orgfiles/ -name '*.org' | vd -f forg`
- or `vd orgfiles/ -f orgdir`
'''

import collections
import datetime
import os
import re

from visidata import vd, VisiData, Column, Sheet, ItemColumn, vlen, asyncthread, Path, AttrDict, date


@VisiData.api
def open_org(vd, p):
    return OrgSheet(p.base_stem, source=p, filetype='org')


@VisiData.api
def open_forg(vd, p):
    return OrgSheet(p.base_stem, source=p, filetype='forg')


@VisiData.api
def open_orgdir(vd, p):
    return OrgSheet(p.base_stem, source=p, filetype='orgdir')


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
        orgmode_parse_into(row, v)

    def putValue(self, row, v):
        self.sheet.save(row)


def sectionize(lines):
    'Generate (startinglinenum, contentlines) for each section.  First section may not have leading * or # but all others will.'
    startinglinenum = 0
    prev_contents = contents = []
    for linenum, line in enumerate(lines):
        line = line.rstrip('\n')

        if line and line[0] in '#*':
            if contents:
                yield startinglinenum, contents
                prev_contents = contents
                contents = []
                startinglinenum = linenum
        else:
            if not line and not contents:
                prev_contents.append(line)

        contents.append(line)

    if contents:
        yield startinglinenum, contents


def orgmode_parse(all_lines):
    root = parent = OrgSheet().newRow()
    for linenum, lines in sectionize(all_lines):
        section = OrgSheet().newRow()

        section.contents = ''
        for i, line in enumerate(lines):
            if not line and not lines[i-1]:
                continue
            section.contents += line + '\n'
        section.orig_contents = section.contents

        section.linenum = linenum+1
        for line in lines:
            section.tags.extend(re.findall(r':([\S:]+?):', line))
            links = re.findall(r'\[.*?\]\(.*?\)', line)
            if links:
                section.links.extend(links)

        title = orgmode_parse_title(lines[0])
        if not title:
            root = parent = section
            continue

        section.update(title)

        while parent and section.level <= parent.level:
            parent = parent.parent

        parent.children.append(section)
        section.parent = parent
        parent = section

    return root

def _replace(node, newnode):
    node.update(newnode)  # must replace insides of same row object
    for c in node.children:
        c.parent = node
    return node

def orgmode_parse_into(toprow, text):
    row = orgmode_parse(text.splitlines())
    if not row.title and len(row.children) == 1:
        row = row.children[0]
        row.parent = toprow.parent
    toprow = _replace(toprow, row)

    return toprow


def orgmode_to_string(section, prestars=''):
    ret = ''

#    if section.title:
#        ret += prestars[len(section.stars):] + (section.title or ' ') + '\n'
    ret += section.contents.rstrip() or ''
    ret += '\n\n'
    ret += ''.join(orgmode_to_string(c, prestars+(section.stars or '')) for c in section.children).rstrip() + '\n'

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
    guide = '''# Orgmode Sheet (experimental)
A list of orgmode sections from _{sheet.source}_.

- `Enter` to expand current section
- `z Enter` to contract current section
- `ga` to combine selected sections into a new entry
- `Ctrl+O` to edit section in system editor (edits source directly)
- `g Ctrl+S` to save all org files
'''
    defer = True
    columns = [
        Column('path', getter=lambda c,r: _root(r).path, width=0),
        Column('id', getter=lambda c,r: _root(r).path.stem),
        ItemColumn('title', width=40),
#        ItemColumn('date', width=0, type=date),
        ItemColumn('tags', width=10, type=lambda v: ' '.join(v)),
        ItemColumn('links', type=vlen),
#        ItemColumn('parent', width=0),
        ItemColumn('children', type=vlen),
        ItemColumn('linenum', width=0, type=int),
        Column('to_string', width=0, getter=lambda c,r: orgmode_to_string(r)),
        OrgContentsColumn('orig_contents', width=0, getter=lambda c,r: r.orig_contents),
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
        return AttrDict(title='', contents='', tags=[], children=[], links=[], level=0, linenum=0)

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
                if p.base_stem.startswith('.'): continue
                if p.ext in ['org', 'md']:
                    yield self.parse_orgmd(p)
        elif self.filetype == 'forg':
            for fn in self.source.open():
                yield self.parse_orgmd(Path(fn.rstrip()))
        elif self.filetype == 'org':
            yield self.parse_orgmd(self.source)

        self.sourceRows = self.rows
        self.refreshRows()

    def parse_orgmd(self, path):
#        row.file_string = open(path).read()
        row = orgmode_parse(open(path).readlines())
        st = path.stat()
        if st:
            mtime = st.st_mtime

        row.path = path
        row.date = mtime
        return row

    def draw(self, scr):
        super().draw(scr)

    @asyncthread
    def putChanges(self):
        adds, mods, dels = self.getDeferredChanges()

        saveset = {}  # path:_root(row)
        for r in adds.values():
            saveset[_root(r).path] = _root(r)
        for r, _ in mods.values():
            saveset[_root(r).path] = _root(r)

        for row in saveset.values():
            self.save(row)

        self.commitAdds()

        self.commitMods()

        for row in dels.values():
            row.path.rename('%s-%s' % (row.path, encode_date()))

        self.commitDeletes()

    def save_all(self):
        for row in self.sourceRows:
            self.save(row)
        vd.status('saved %s org files' % len(self.sourceRows))

    def save(self, row):
        try:
            row.path.rename('%s-%s' % (row.path, encode_date()))  # backup
        except FileNotFoundError:
            pass

        with row.path.open(mode='w') as f:
            print(orgmode_to_string(row).rstrip(), file=f)


@OrgSheet.api
def paste_into(sheet, row, sourcerows, cols):
    row.children.extend(sourcerows)
    for r in sourcerows:
        r.parent.children.remove(r)
        r.parent = row
    sheet.refreshRows()


@OrgSheet.api
def paste_data_into(sheet, row, sourcerows, cols):
    body = row.body or ''
    for r in sourcerows:
        data = vd.encode_json(r, cols)
        row.contents += f':{cols[0].sheet.name}:{data}\n'


@OrgSheet.api
def combine_rows(sheet, rows):
    newrow = sheet.newRow()
    newrow.date = datetime.datetime.today()
    orgid = vd.cleanName(rows[0].title)
    newrow.path = Path((orgid or encode_date())+'.org')
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
    with p.open(mode='w', encoding=vsheets[0].options.save_encoding) as fp:
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

    idtexts = {}
    for idtag, text in re.findall(r'\{::(\d+)::\}(.*?)(?={::)', ret, re.DOTALL):
        idtexts[int(idtag)] = text

    # reparse all existing
    for rowid, row in idrows.items():
        text = idtexts.get(rowid, '').strip()
        if text:
            orgmode_parse_into(row, text)
        else:
            # sometimes, top levels are missing parents
            # this needs to be debugged
            if row.parent:
                row.parent.children.remove(row)

    lastrow = None
    # find new rows to add
    for rowid, text in idtexts.items():
        if rowid not in idrows:
            section = orgmode_parse(text.splitlines())
            while section.level <= lastrow.level:
                lastrow = lastrow.parent

            if lastrow:
                sourceRows.append(section)
            else:
                sheet.addRow(section)

    sheet.refreshRows()

OrgSheet.addCommand('^O', 'sysopen-row', 'sysopen_row(cursorRow)', 'open current file in external $EDITOR')
OrgSheet.addCommand('g^O', 'sysopen-rows', 'sysopen_rows(selectedRows)', 'open selected files in external $EDITOR')
OrgSheet.addCommand('^J', 'expand-row', 'openRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('z^J', 'close-row', 'closeRows([cursorRow]); sheet.cursorRowIndex += 1')
OrgSheet.addCommand('g^J', 'expand-selected', 'openRows(selectedRows)')
OrgSheet.addCommand('gz^J', 'close-selected', 'closeRows(selectedRows)')
OrgSheet.addCommand('ga', 'combine-selected', 'addRows([combine_rows(selectedRows)], index=cursorRowIndex); cursorDown(1)', 'combine selected rows into new org entry')

OrgSheet.addCommand('zp', 'paste-data', 'paste_data_into(cursorRow, vd.memory.cliprows, vd.memory.clipcols)', 'move clipboard rows to children of current row')
OrgSheet.addCommand('p', 'paste-sections', 'paste_data_into(cursorRow, vd.memory.cliprows, vd.memory.clipcols)', 'move clipboard rows to children of current row')
OrgSheet.addCommand('g^S', 'save-all', 'save_all()', 'save all org files')


if __name__ == '__main__':
    for fn in sys.argv[1:]:
        sect = orgmode_parse(Path(fn))
        print(orgmode_to_string(sect).strip())
