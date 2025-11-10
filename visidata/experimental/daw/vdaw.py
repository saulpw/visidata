from collections import defaultdict
from copy import copy

import json
import textwrap

from functools import cached_property
from visidata import vd, VisiData, Sheet, ItemColumn, AttrColumn, AttrDict, vlen, RowColorizer, Column
from visidata import drawcache_property, setitem, asyncthread

from . import MpvProcess

vd.theme_option('color_daw_header', 'underline', 'color of first line in a transcript section')
vd.theme_option('color_daw_playhead', 'blue', 'color of playhead line')
vd.theme_option('color_daw_cut', '238', 'color of cut rows')
vd.theme_option('color_daw_keep', 'green', 'color of kept rows')
vd.theme_option('daw_include_cuts', True, 'whether saving xmd format includes cuts with strikethrough')


TODO = '''
- single-word interjections inlined into other paragraph
- bug: fix split
- combine consecutive cuts in markdown
- bug: batch convert transcript to xmd "terminated"

- feat: play side subsheet of rows (if in order)
- feat: edit text of subwords while maintaining timings
- output should descend into EditRow; lower headers are subheaders?

- feat: replace line with separate stem (e.g. AI generated voice)

- ) to reclose current row.  or is that too much given ENTER/q?


- command to rollup whisper transcript by speaker again
   - like the .xmd output grouping

? sequential cut lines should show up as single …
? select to next marker
? command to select rows from last marker (zs)

- cleanup: rename PodcastEditingSheet to Transcript[Editing]Sheet

? highlight current word in transcript

- track cutpoints as times
- feat: z< and z> to adjust the previous cutpoint
   - play 100ms tone at marker

- feat: 1-9 for numbered (temporary) marker
   - 'z1' to set marker 1 at current timestamp; '1' to play starting at marker 1

7. outputs
   + c) transcript with cuts excluded (transcript of edited audio) -- based on options.daw_include_cuts
   d) edited audio (pasting non-cut sections together)
   e) .omf file for use in other DAW like reaper
'''

options_daw_hms_seps = '::.'  # or maybe 'hm.' or '..,'

def to_hms(t:float, width=None) -> str:
    'Return some form of HH:MM:SS.s'
    if t is None or t == 0:
        return ''

    if t < 100:
        return f'{t:0.1f}s'

    ret = ''

    h = int(t // 3600)
    if h > 0:
        ret += f'{h}' + options_daw_hms_seps[0]

    m = int((t % 3600) // 60)
    if ret or m > 0:
        ret += f'{m:02d}' + options_daw_hms_seps[1]

    s = int(t % 60)
    ms = int((t - int(t))*10)

    ret += f'{s:02d}{options_daw_hms_seps[2]}{ms:01d}'

    return ret

def cleanword(s:str) -> str:
    return ''.join(c for c in s if c.isalnum())

def is_cut(row):
    if isinstance(row.cut, (float, int)):
        return row.cut < 0
    else:
        return bool(row.cut)


def replace_subrows(row):
    'Turn row into EditRow, recursively making its subrows also EditRows, until the bottom level which are simple AttrDicts.'
    if not isinstance(row, EditRow):
        ret = EditRow(**row)
    else:
        ret = row

    if not ret.subrows:
        if not ret.data:
            ret.data = AttrDict(row)
    else:
        ret.subrows = [replace_subrows(baser) for baser in ret.subrows]
    return ret


@VisiData.api
def open_transcript(vd, p):
    '''path is transcript in JSON format; audio should be path.mp3'''
    vd.timeouts_before_idle = -1
    return PodcastEditingSheet(p.name, source=p)

@Column.api
def formatter_hhmmss(self, fmtstr):
    return to_hms


class EditRow:
    def __init__(self, section:str='', speaker:str='', header:str='', subrows:list=None, cut=None, **kwargs):
        self.data = None  # start/end/text for leaf nodes
        self.section = section
        self.speaker = speaker
        self.header = header
        self.weird = None
        self.subrows = [replace_subrows(baser) for baser in (subrows or [])]
        if not subrows or cut is not None:
            self.cut = cut
        else:
            self.cut = max(r.cut if r.cut else 0 for r in self.subrows)

    def __str__(self):
        return f'[{self.cut} {self.start:.1f}-{self.end:.1f}] {self.speaker}: {self.editedtext}'
        return f'[{"CUT " if is_cut(self) else ""}{self.start:.1f}-{self.end:.1f}] {self.speaker}: {self.editedtext}'

    def to_json(self) -> dict:
        return dict(section=self.section,
                    speaker=self.speaker,
                    start=self.start,
                    end=self.end,
                    cut=self.cut,
                    subrows=self.subrows,
                    text=self.text)

    def __contains__(self, t:float) -> bool:
        if not self.start or not self.end:
            return False
        return self.start <= t <= self.end

    @drawcache_property
    def start(self) -> float:
        if self.data: return self.data.start
        return min((r.start for r in self.subrows if r.start), default=None)

    @drawcache_property
    def end(self) -> float:
        if self.data: return self.data.end
        return max((r.end for r in self.subrows if r.end), default=None)

    @drawcache_property
    def duration(self) -> float:
        if self.data: return self.data.end-self.data.start
        return sum((r.duration or 0) for r in self.uncutrows) if self.uncutrows else 0

    @drawcache_property
    def raw_duration(self) -> float:
        return self.end-self.start

    @cached_property
    def text(self) -> str:
        if self.data: return self.data.text
        if self.cut:
            # if shown directly, toplevel shows words for all rows regardless of cutness
            return ' '.join((r.text or '') for r in self.subrows)
        else:
            # otherwise cut subrows are elided
            return ' '.join((r.text or '') if not r.cut else '…' for r in self.uncutrows)

    @cached_property
    def editedtext(self) -> str:
        if self.data:
            if is_cut(self):
                return f'~~{self.data.text}~~'
            else:
                return self.data.text

        line = ' '.join((r.text or '') for r in self.subrows)
        if is_cut(self):
            line = f'~~{line}~~'
        return line

    @drawcache_property
    def uncutrows(self) -> list:
        if is_cut(self):
            return []
        return [r for r in self.subrows if r and not is_cut(r)]

    @cached_property
    def nwords(self) -> int:
        return sum(r.nwords for r in self.subrows) if not self.data else len(self.data.text.split())

    def split_at_word(self, n:int) -> tuple['EditRow', 'EditRow']:
        wordnum = 0
        beforerows = []
        afterrows = []
        midrow = None
        for sr in self.uncutrows:
            nsubwords = len(sr.text.split())
            if wordnum < n:
                beforerows.append(sr)
            elif wordnum + nsubwords - 1 > n:
                afterrows.append(sr)
            else:
                assert midrow is None
                midrow = sr
                cutwordnum = n - wordnum

            wordnum += nsubwords

        if midrow:  # word n is contained within this subrow
            if midrow.subrows:
                a, b = midrow.split_at_word(cutwordnum)
                r1 = EditRow(section=self.section, speaker=self.speaker, header=self.header, subrows=beforerows + [a], cut=self.cut)
                r2 = EditRow(section=self.section, speaker=self.speaker, subrows=[b] + afterrows, cut=self.cut)
                return r1, r2
            else:
                r1 = EditRow(section=self.section, speaker=self.speaker, header=self.header, subrows=beforerows + [midrow], cut=self.cut)
                r2 = EditRow(section=self.section, speaker=self.speaker, subrows=afterrows, cut=self.cut)
                return r1, r2
        else:
            return None, None

    def split_at_time(self, t:float) -> tuple['EditRow', 'EditRow']:
        midrow = None
        beforerows = None
        afterrows = None
        for i, r in enumerate(self.subrows):
            if r.subrows:
                if t in r:
                    beforerows = self.subrows[:i]
                    afterrows = self.subrows[i+1:]
                    midrow = r
                    break
            else:  # bottomost level
                if t <= r.start:
                    if i == 0:
                        beforerows = []
                        afterrows = self.subrows
                        break
                    elif self.subrows[i-1].end <= t <= r.start:
                        beforerows = self.subrows[:i]
                        afterrows = self.subrows[i:]
                        break
                    else:  # in the middle of the previous word
                        prevr = self.subrows[i-1]
                        beforerows = self.subrows[:i-1]
                        afterrows = self.subrows[i-1:]
                        assert prevr.start <= t <= prevr.end, (prevr.start, t, prevr.end)
                        break

        if midrow:  # time t is contained within this subrow
            if midrow.subrows:
                a, b = midrow.split_at_time(t)
                r1 = EditRow(section=midrow.section, speaker=midrow.speaker, header=self.header, subrows=beforerows + [a])
                r2 = EditRow(section=midrow.section, speaker=midrow.speaker, subrows=[b] + afterrows)
                return r1, r2
            else:
                r1 = EditRow(section=self.section, speaker=midrow.speaker, header=self.header, subrows=beforerows + [midrow])
                r2 = EditRow(section=self.section, speaker=midrow.speaker, subrows=afterrows)
                return r1, r2
        else:
            r1 = EditRow(section=self.section, speaker=self.speaker, header=self.header, subrows=beforerows)
            r2 = EditRow(section=self.section, speaker=self.speaker, subrows=afterrows)
            return r1, r2


class PodcastEditingSheet(Sheet):
    columns = [
        AttrColumn('section', width=20),
        AttrColumn('speaker'),
        AttrColumn('start', type=float, formatter='hhmmss'),
        AttrColumn('end', type=float, formatter='hhmmss'),
        AttrColumn('duration', type=float, formatter='hhmmss'),
        AttrColumn('raw', 'raw_duration', type=float, formatter='hhmmss'),
        AttrColumn('cut', type=float, width=6),
        AttrColumn('score', type=float, width=0),
        AttrColumn('text', width=80),
        AttrColumn('subrows', type=vlen, width=0),
    ]
    colorizers = [
        RowColorizer(5, 'color_daw_header', lambda s,c,r,v: r.header),  # section header
        RowColorizer(3, 'color_daw_cut', lambda s,c,r,v: r.cut and r.cut < 0),
        RowColorizer(5, 'color_daw_keep', lambda s,c,r,v: r.cut and r.cut > 0),
        RowColorizer(4, 'color_daw_playhead', lambda s,c,r,v: s.mpv.playback_time in r)
    ]
    nKeys = 2
    mpv = AttrDict()  # bunk null mock object until server created
    sourcerows = None
    sourceaudio = None

    curfilter = 'agate'
    curparm = 'ratio'
    speed = 1
    skipcut = True  # play audio without cut segments

    def iterload(self):
        self.speakers = defaultdict(list)  # speakername -> list of words/subrows

        if not self.sourcerows:
            d = json.loads(self.source.open_text().read())
            self.sourceaudio = d.get('sourceaudio', None)

            self.sourcerows = d['word_segments']

        if not self.sourceaudio:
            if self.source.with_suffix('.mp3').exists():
                self.sourceaudio = str(self.source.with_suffix('.mp3'))
            elif self.source.with_suffix('.wav').exists():
                self.sourceaudio = str(self.source.with_suffix('.wav'))

        if self.sourceaudio:
            self.mpv = MpvProcess(self.sourceaudio, self)
            self.mpv.start_mpv()
        else:
            vd.warning("no matching audio file")

        curhdr = ''
        try:
            for row in self.sourcerows:
                if not isinstance(row, EditRow):
                    row = EditRow(**row)
                if row.section != curhdr:  # only the first row of a section has 'header'
                    curhdr = row.header = row.section

                self.speakers[row.speaker].append(row)
                yield row
        except Exception as e:
            vd.exceptionCaught(e)

        self.column('duration').aggregators = 'sum'
        self.column('raw').aggregators = 'sum'
        self.column('start').aggregators = 'min'
        self.column('end').aggregators = 'max'

    def openRows(self, rows):
        def itersubrows(rows):
            for r in rows:
                yield from r.subrows

        vs = PodcastEditingSheet(*self.names, rows[0].section,
                                   source=self.source,
                                   sourcerows=iterwords(rows),
                                   sourceaudio=self.sourceaudio)
        vd.push(vs)

    def openRow(self, row):
        return PodcastEditingSheet(*self.names, row.section,
                                   source=self.source,
                                   sourcerows=row.subrows,
                                   sourceaudio=self.sourceaudio)

    def combine_rows(self, rows):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))
        self.modified = True

        uncutrows = [r for r in rows if not r.cut or r.cut < 0]
        newrow = EditRow(speaker=' '.join(set(r.speaker for r in uncutrows if r.speaker)),
                         section=rows[0].section,
                         subrows=rows)
        self.addRow(newrow, index=self.cursorRowIndex)

        for r in rows:
            self.rows.remove(r)

    def expand_row(self, rowidx):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))
        self.modified = True

        subrows = self.rows[rowidx].subrows
        if subrows:
            if self.rows[rowidx].section:
                subrows[0].section = self.rows[rowidx].section
            self.rows[rowidx:rowidx+1] = subrows
        else:
            vd.warning('no subrows')

    def bump(self, n, *rows):
        self.modified = True
        for row in rows:
            vd.addUndo(setattr, row, 'cut', row.cut)
            row.cut = (row.cut or 0)+n
        self.column('duration')._aggregatedTotals.clear()

    def cycle_speaker(self, row):
        self.modified = True
        vd.addUndo(setattr, row, 'speaker', row.speaker)
        speakers = list(self.speakers.keys())
        row.speaker = speakers[(speakers.index(row.speaker)+1)%len(speakers)]

    def getRowIndexByPlaytime(self, t:float, rows=None) -> int:
        'Return index of first row that ostensibly contains time t.'
        rows = rows or self.rows
        rowpath = self.find_row_path(t, rows)
        return rows.index(rowpath[0])

    def checkCursor(self):
        super().checkCursor()

        if not self.skipcut:
            return

        t = self.mpv.playback_time
        if not t:
            return

        words = self.words
        rowpath = self.find_row_path(t)
        widx = words.index(rowpath[-1])
        cut = False

        while any(map(is_cut, rowpath)):
            widx += 1
            cut = True
            rowpath = self.find_row_path(words[widx].start)

        if widx >= len(words):
            self.mpv.pause_audio()

        if cut:
            newt = words[widx].start  # or words[widx-1].end
            self.mpv.play_audio(newt)

    def find_row_path(self, t:float, rows:list['EditRow']=None) -> list['EditRow']:
        '''Return a list of EditRow along the path to the actual word at time t.
        Each EditRow either contains t, or is immediately after t.
        The toplevel segment containing t is ret[0], and the exact word at/near t is ret[-1].
        '''
        if rows is None:
            rows = self.rows

        # binary search
        low = 0
        high = len(rows) - 1

        while low <= high:
            mid = (high + low) // 2
            midw = rows[mid]
            if mid > 0 and t < rows[mid-1].end:  # t in/before preceding word
                high = mid - 1
            elif t > midw.end:  # t after mid word
                low = mid + 1
            else:  # t either within mid word or just before it
                if not midw.subrows:
                    return [midw]
                else:
                    return [midw] + self.find_row_path(t, midw.subrows)

    def is_cut(self, t:float):
        rowpath = self.find_row_path(t)
        if t not in rowpath[-1]:
            return False
        return any(map(is_cut, rowpath))

    def go_playhead(self):
        t = self.mpv.playback_time
        self.cursorRowIndex = self.getRowIndexByPlaytime(t)

    def split_at_playhead(self):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))

        t = self.mpv.playback_time
        idx = self.getRowIndexByPlaytime(t)
        row = self.rows[idx]

        if t in row:
            idx += 1
            row = self.rows[idx]

        row, newrow = row.split_at_time(t)
        self.rows[idx] = row  # might be the same, modified in place
        self.addRow(newrow, index=idx+1)

    def split_at_input(self, rowidx, word:str):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))

        oldrow = self.rows[rowidx]

        try:
            wordidx = int(word)
        except Exception:
            words = [cleanword(w) for w in oldrow.text.split()]
            wordidx = words.index(cleanword(word))

        if wordidx == 0:
            vd.fail('cannot split on first word')

        row, newrow = oldrow.split_at_word(wordidx-1)
        self.rows[rowidx] = row  # might be the same, modified in place
        self.addRow(newrow, index=rowidx+1)

    def go_header_next(self, didx:int, startrow:int):
        i = startrow
        while 0 <= i < self.nRows-(0 if didx < 0 else 1):
            i += didx
            if self.rows[i].header:
                self.cursorRowIndex = i
                return
        vd.fail("no more sections")

    @property
    def playheadStatus(self):
        try:
            return to_hms(self.mpv.playback_time)
        except Exception as e:
            if vd.options.debug:
                vd.exceptionCaught(e)

    def setFilterParmByIndex(self, filtername, parmname, idxvalue):
        self.mpv.set_filter_parm(filtername, parmname, self.mpv.afilter_options[filtername][parmname][idxvalue])

    def reformat_row(self, rowidx, undo=True):
        if undo:
            vd.addUndo(setattr, self, 'rows', copy(self.rows))

        row = self.rows[rowidx]

        formatted_rows = []
        wordnum = 0
        for line in textwrap.wrap(row.text,
                        width=self.column('text').width-2,
                        break_long_words=False,
                        break_on_hyphens=False):
            pr, row = row.split_at_word(len(line.split())-1)
            if pr:
                formatted_rows.append(pr)

            if not isinstance(row, EditRow):
                break

        self.rows[rowidx:rowidx+1] = formatted_rows

    def reformat_rows(self, rows):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))
        for row in rows[::-1]:
            if not row.cut or row.cut > 0:
                self.reformat_row(rows.index(row), undo=False)

    def speed_change(self, dv):
        self.speed *= dv
        self.mpv.set_property('speed', self.speed)

    @drawcache_property
    def words(self):
        'All word-level EditRows'
        return list(iterwords(self.rows))

    @asyncthread
    def flag_bad_timings(self):
        def weird(t1, t2):
            return t1 and t2 and (t1 > t2 or t2-t1 > 0.5)

        words = self.words
        lastnonweirdt = 0
        for i, w2 in enumerate(words):
            if i == 0 or i >= len(words)-1:
                continue

            w1 = words[i-1]
            w3 = words[i+1]

            if weird(w2.start, w2.end):  # if too long
                w2.weird = True
            elif weird(w1.end, w2.start) and weird(w2.end, w3.start):
                w2.weird = True
            elif w2.start > w2.end or w2.start < lastnonweirdt:
                w2.weird = True
            else:
                lastnonweirdt = w2.start  # or end?

        for w in words:
            if w.weird:
                w.data.start = None
                w.data.end = None

        # pass 2: look for runs of "None" timings and interpolate from surrounding words
        firstidx = None
        for i, w in enumerate(words):
            if w.start is None and firstidx is None:
                firstidx = i
            elif w.start is not None and firstidx is not None:
                startt = words[firstidx-1].end + 0.1  # 100ms between words
                endt = words[i].start - 0.1
                # interpolate timings for None-timed sequence of words
                dt = (endt-startt-0.01*(i-firstidx))/(i-firstidx)
                # vd.status(f'{dt*1000:.0f}ms for each of {i-firstidx} words from {startt:.1f}-{endt:.1f}s')
                for j, wnone in enumerate(words[firstidx:i]):
                    wnone.data.start = startt+dt*j + 0.005
                    wnone.data.end = startt+dt*(j+1) - 0.005

                firstidx = None
            # else in the middle of a run, let it run

def iterwords(segs):
    for seg in segs:
        if not seg.subrows:
            yield seg
        else:
            yield from iterwords(seg.subrows)


@VisiData.api
class FilterParametersSheet(Sheet):
    columns = [
        ItemColumn('filter'),
        ItemColumn('filter_parm'),
        ItemColumn('value', setter=lambda c,r,v: c.sheet.source.mpv.set_filter_parm(r.filter, r.filter_parm, type(r.default_value)(v))),
        ItemColumn('default_value'),
        ItemColumn('help'),
    ]
    colorizers = [
        RowColorizer(5, 'on 90', lambda s,c,r,v: r.value is not None and r.value != r.default_value)
    ]
    def iterload(self):
        for filtername, values in self.source.mpv.afilter_options.items():
            helpstrs = dict((i.key, i.desc) for i in self.source.mpv.afilters[filtername])
            for filterparmname, parmvalue in values.items():
                yield AttrDict(filter=filtername,
                           filter_parm=filterparmname,
                           value=self.source.mpv.afilter_parms.get(filtername, {}).get(filterparmname, None),
                           default_value=self.source.mpv.afilter_options[filtername][filterparmname][0],
                           help=helpstrs[filterparmname])


@VisiData.api
def save_cutlist(vd, p, sheet):
    assert isinstance(sheet, PodcastEditingSheet)

    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        fp.write(f'## edits for {sheet.mpv.sourceaudio}\n\n')

        i = 0
        cut_start = None
        cut_end = None
        for row in sheet.rows:
            if row.cut:
                if cut_start is None:
                    cut_start = row
                cut_end = row
            else:
                if cut_start is not None:
                    i += 1
                    dt = '??'
                    if cut_end.end and cut_start.start:
                        dt = f'{cut_end.end - cut_start.start:.1f}'
                    fp.write(f'{i}. cut {dt}s from {to_hms(cut_start.start)} to {to_hms(cut_end.end)}: {cut_start.text[:10]}...{cut_end.text[-10:]}\n')
                    cut_start = None
                    cut_end = None

def iterspeakerrows(rows):
    def _combine_rows(accumrows):
        firstrow = accumrows[0]
        r = EditRow(speaker=firstrow.speaker,
                    section=firstrow.section)
        text = ' '.join(r.editedtext for r in accumrows)
        if is_cut(firstrow):
            text = text.replace('~~', '')
            text = '~~' + text + '~~'
        r.data = AttrDict(start=firstrow.start, end=lastrow.end, text=text)
        return r

    accumrows = []
    for i, row in enumerate(rows):
        assert row, i
        if ' ' in row.speaker:
            yield from iterspeakerrows(row.subrows)
            continue

        if not accumrows:
            accumrows = [row]
            continue

        lastrow = accumrows[-1]
        if is_cut(row) == is_cut(lastrow) and row.speaker == lastrow.speaker and row.section == lastrow.section:
            accumrows.append(row)
            continue

        if is_cut(row) == is_cut(lastrow) and row.section == lastrow.section:
            # speaker different; only one word?
            if row.nwords == 1:
                r = EditRow(speaker=lastrow.speaker, section=row.section, cut=is_cut(row))   # fake speaker
                r.data = AttrDict(start=row.start, end=row.end, text=f'[{row.speaker}: {row.text}]')
                accumrows.append(r)
                continue

        yield _combine_rows(accumrows)

        accumrows = [row]

    yield _combine_rows(accumrows)


@VisiData.api
def save_xmd(vd, p, sheet):
    assert isinstance(sheet, PodcastEditingSheet)

    prevhdr = ''
    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        for row in iterspeakerrows(sheet.rows):

            if row.section != prevhdr:
                prevhdr = row.section
                fp.write(f'## {prevhdr}\n\n')

            timestr = to_hms(row.start)
            line = f'[{timestr}] **{row.speaker}**: {row.text}'
            line = line.strip()
            if row.cut:
                if sheet.options.daw_include_cuts:
                    line = f'~~{line}~~'
                else:
                    line = ''

            if line:
                fp.write(line+'\n\n')


# use .to_json() for any class that is not already serializable, like EditRow
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default

@VisiData.api
def save_transcript(vd, p, sheet):
    d = dict(word_segments=sheet.rows, sourceaudio=sheet.mpv.sourceaudio)
    with p.open(mode='w', encoding='utf-8') as fp:
        fp.write(json.dumps(d)+'\n')


PodcastEditingSheet.options.save_filetype = 'transcript'
PodcastEditingSheet.options.disp_rstatus_fmt = '{sheet.playheadStatus}  ' + Sheet.options.disp_rstatus_fmt

PodcastEditingSheet.addCommand('P', 'play-row-raw', 'mpv.play_audio(cursorRow.start); sheet.skipcut=False')
PodcastEditingSheet.addCommand('p', 'play-row', 'mpv.play_audio(cursorRow.start); sheet.skipcut=True')
PodcastEditingSheet.addCommand('zp', 'play-toggle', 'mpv.pause_audio(not mpv.paused)')
FilterParametersSheet.addCommand('P', 'play-toggle', 'source.mpv.pause_audio(not source.mpv.paused)')
PodcastEditingSheet.addCommand('g)', 'combine-selected', 'combine_rows(selectedRows)')
PodcastEditingSheet.addCommand('(', 'expand-row', 'expand_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('g(', 'expand-selected', 'for row in selectedRows: expand_row(rows.index(row))')

PodcastEditingSheet.addCommand('Ctrl+R', 'restart-mpv', 'mpv.start_mpv()')

FilterParametersSheet.addCommand('a', 'add-filter', 'source.mpv.add_filter()', 'add filter on current row')
FilterParametersSheet.addCommand('d', 'remove-filter', 'source.mpv.remove_filter()', 'remove filter on current row')

for i in range(0, 10):
    PodcastEditingSheet.addCommand(str(i), f'set-afilter-parm-{i}', f'setFilterParmByIndex(curfilter, curparm, {i})')
    FilterParametersSheet.addCommand(str(i), f'set-afilter-parm-{i}', f'source.setFilterParmByIndex(cursorRow.filter, cursorRow.filter_parm, {i}); reload()')

PodcastEditingSheet.addCommand('', 'cycle-speaker', 'cycle_speaker(cursorRow)')
PodcastEditingSheet.addCommand('[', 'audio-back-10', 'mpv.seek_audio(-10); go_playhead()')
PodcastEditingSheet.addCommand(']', 'audio-forward-10', 'mpv.seek_audio(+10); go_playhead()')
PodcastEditingSheet.addCommand('g[', 'audio-back-60', 'mpv.seek_audio(-60); go_playhead()')
PodcastEditingSheet.addCommand('g]', 'audio-forward-60', 'mpv.seek_audio(+60); go_playhead()')
PodcastEditingSheet.addCommand('gg', 'go-playhead', 'go_playhead()', 'move row cursor to playhead' )

PodcastEditingSheet.addCommand('F5', 'audio-slower', 'speed_change(0.5)', 'adjust playspeed down 50%')
PodcastEditingSheet.addCommand('F8', 'audio-faster', 'speed_change(2.0)', 'adjust playspeed 2x')

PodcastEditingSheet.addCommand('a', 'split-at-time', 'split_at_playhead(); cursorDown(2)', 'split line at current playhead')
PodcastEditingSheet.addCommand('za', 'split-at-input', 'split_at_input(cursorRowIndex, input("word to split at: "))', 'split line at current playhead')
PodcastEditingSheet.addCommand('x', 'cut-row', 'bump(-1, cursorRow)', 'cut audio for line at cursor row')
PodcastEditingSheet.addCommand('y', 'bump-row', 'bump(+1, cursorRow)', 'upvote audio for line at cursor row')
PodcastEditingSheet.addCommand('gx', 'cut-selected', 'bump(-1, *selectedRows)', 'cut audio for selected rows')
PodcastEditingSheet.addCommand('gy', 'bump-selected', 'bump(+1, *selectedRows)', 'bump audio for selected rows')
PodcastEditingSheet.addCommand('<', 'go-header-prev', 'go_header_next(-1, cursorRowIndex)', 'move row cursor to previous section')
PodcastEditingSheet.addCommand('>', 'go-header-next', 'go_header_next(+1, cursorRowIndex)', 'move row cursor to next section')
PodcastEditingSheet.addCommand('g<', 'go-header-first', 'go_header_next(+1, 0)', 'move row cursor to first section')
PodcastEditingSheet.addCommand('g>', 'go-header-last', 'go_header_next(-1, nRows-1)', 'move row cursor to last section')

PodcastEditingSheet.addCommand('f', 'open-vdaw-filters', 'vd.push(FilterParametersSheet("filters", source=sheet))')
PodcastEditingSheet.addCommand('r', 'reformat-row', 'reformat_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('gr', 'reformat-selected', 'reformat_rows(selectedRows)')

PodcastEditingSheet.addCommand('c', 'clean-timings', 'flag_bad_timings()')
