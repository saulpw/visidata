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
- bug: word timings WAY off (adding 40% to duration when summed!)

- skip cut segments while playing
  - play segments individually
  - feature: play side subsheet of rows

- cleanup: rename PodcastEditingSheet to Transcript[Editing]Sheet

- ) to reclose current row.  or is that too much given ENTER/q?

- output should descend into EditRow; lower headers are subheaders?

- sequential cut lines should show up as single …
- select to next marker
- command to rollup whisper transcript by speaker again
- command to select rows from last marker (zs)
- move an edit time

cleanups:
  - JSONDecodeError: sometimes query gets extra data with json.  make line buffering?

- sync gets lost if a word is <100ms +1
- changing speakers should set speaker on all baserows?
- highlight current word in transcript?

4. add marker
   - z< and z> to adjust the previous marker
   - play 100ms tone at marker

6. numbered markers?
   - 1-9 for numbered (temporary) marker
   - 'z1' to set marker 1 at current timestamp; '1' to play starting at marker 1

7. outputs
   + a) cutlist (list of edits to apply)
   + b) transcript with cuts included (has strikethrough for cut lines)
   + c) transcript with cuts excluded (transcript of edited audio) -- based on options.daw_include_cuts
   d) edited audio (pasting non-cut sections together)
   e) .omf file for use in other DAW like reaper

'''

def to_hms(t:float, width=None) -> str:
    'Return some form of HH:MM:SS.s'
    if t is None or t == 0:
        return ''

    if t < 100:
        return f'{t:0.1f}s'

    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t))*10)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:01d}'


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
        self.subrows = [replace_subrows(baser) for baser in (subrows or [])]
        if not subrows or cut is not None:
            self.cut = cut
        else:
            self.cut = max(r.cut if r.cut else 0 for r in self.subrows)

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

    @cached_property
    def start(self) -> float:
        if self.data: return self.data.start
        return min(r.start for r in self.subrows)

    @cached_property
    def end(self) -> float:
        if self.data: return self.data.end
        return max(r.end for r in self.subrows)

    @drawcache_property
    def duration(self) -> float:
        if self.data: return self.data.end-self.data.start
        return sum((r.duration or 0) for r in self.uncutrows) if self.uncutrows else 0

    @cached_property
    def text(self) -> str:
        if self.data: return self.data.text
        if self.cut:
            # if shown directly, toplevel shows words for all rows regardless of cutness
            return ' '.join((r.text or '') for r in self.subrows)
        else:
            # otherwise cut subrows are elided
            return ' '.join((r.text or '') if not r.cut else '…' for r in self.uncutrows)

    @drawcache_property
    def uncutrows(self) -> list:
        if is_cut(self):
            return []
        return [r for r in self.subrows if r and not is_cut(r)]

    @cached_property
    def nwords(self) -> int:
        return sum(r.nwords if isinstance(r, EditRow) else 1 for r in self.subrows)

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
        AttrColumn('cut', type=float, width=6),
        AttrColumn('score', type=float, width=0),
        AttrColumn('text', width=80),
        AttrColumn('subrows', type=vlen, width=0),
    ]
    colorizers = [
        RowColorizer(5, 'color_daw_header', lambda s,c,r,v: r.header),  # section header
        RowColorizer(5, 'color_daw_cut', lambda s,c,r,v: r.cut and r.cut < 0),
        RowColorizer(5, 'color_daw_keep', lambda s,c,r,v: r.cut and r.cut > 0),
        RowColorizer(3, 'color_daw_playhead', lambda s,c,r,v: s.mpv.playback_time in r)
    ]
    nKeys = 2
    mpv = AttrDict()  # bunk null mock object until server created
    sourcerows = None
    sourceaudio = None

    curfilter = 'agate'
    curparm = 'ratio'
    speed = 1

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
        self.column('start').aggregators = 'min'
        self.column('end').aggregators = 'max'

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
        try:
            return next(i for i,r in enumerate(rows or self.rows) if t in r)
        except StopIteration:
            vd.debug(f'time {to_hms(t)} not found')

    def checkCursor(self):
        super().checkCursor()

        t = self.mpv.playback_time
        if not t:
            return

        origrowidx = self.getRowIndexByPlaytime(t)
        i = origrowidx
        while i < self.nRows:
            pbrow = self.rows[i]
            if not is_cut(pbrow):
                break
            i += 1

        if i >= self.nRows:
            self.mpv.pause_audio()
        elif i != origrowidx:
            self.mpv.play_audio(self.rows[i].start)

    def go_playhead(self):
        t = self.mpv.playback_time
        self.cursorRowIndex = self.getRowIndexByPlaytime(t)

    def split_at_playhead(self):
        vd.addUndo(setattr, self, 'rows', copy(self.rows))

        t = self.mpv.playback_time
        idx = self.getRowIndexByPlaytime(t)
        row = self.rows[idx]

        row, newrow = row.split_at_time(t)
        self.rows[idx] = row  # might be the same, modified in place
        self.addRow(newrow, index=idx+1)

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
                    fp.write(f'{i}. cut from {to_hms(cut_start.start)} to {to_hms(cut_end.end)}: {cut_start.text[:10]}...{cut_end.text[-10:]}\n')
                    cut_start = None
                    cut_end = None

@VisiData.api
def save_xmd(vd, p, sheet):
    assert isinstance(sheet, PodcastEditingSheet)

    prevhdr = ''
    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        for row in sheet.rows:
#            timestr = f'{row.start:0.1f}'
            timestr = to_hms(row.start)

            if row.get('section', prevhdr) != prevhdr:
                prevhdr = row.get('section')
                fp.write(f'## {prevhdr}\n\n')

            line = f'[{timestr}] {row.speaker}: {row.text}'
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

PodcastEditingSheet.addCommand('P', 'play-row', 'mpv.play_audio(cursorRow.start)')
PodcastEditingSheet.addCommand('p', 'play-toggle', 'mpv.pause_audio(not mpv.paused)')
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

PodcastEditingSheet.addCommand('a', 'add-cutpoint', 'split_at_playhead(); cursorDown(2)', 'split line at current playhead')
PodcastEditingSheet.addCommand('d', 'cut-row', 'bump(-1, cursorRow); cursorDown(1)', 'cut audio for line at cursor row')
PodcastEditingSheet.addCommand('y', 'bump-row', 'bump(+1, cursorRow)', 'upvote audio for line at cursor row')
PodcastEditingSheet.addCommand('gd', 'cut-selected', 'bump(-1, *selectedRows)', 'cut audio for selected rows')
PodcastEditingSheet.addCommand('gy', 'bump-selected', 'bump(+1, *selectedRows)', 'bump audio for selected rows')
PodcastEditingSheet.addCommand('<', 'go-header-prev', 'go_header_next(-1, cursorRowIndex)', 'move row cursor to previous section')
PodcastEditingSheet.addCommand('>', 'go-header-next', 'go_header_next(+1, cursorRowIndex)', 'move row cursor to next section')
PodcastEditingSheet.addCommand('g<', 'go-header-first', 'go_header_next(+1, 0)', 'move row cursor to first section')
PodcastEditingSheet.addCommand('g>', 'go-header-last', 'go_header_next(-1, nRows-1)', 'move row cursor to last section')

PodcastEditingSheet.addCommand('f', 'open-vdaw-filters', 'vd.push(FilterParametersSheet("filters", source=sheet))')
PodcastEditingSheet.addCommand('r', 'reformat-row', 'reformat_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('gr', 'reformat-selected', 'reformat_rows(selectedRows)')
