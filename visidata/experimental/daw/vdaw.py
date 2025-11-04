from collections import defaultdict

import json
import textwrap

from visidata import vd, VisiData, Sheet, ItemColumn, AttrColumn, AttrDict, vlen, RowColorizer, Column
from visidata import drawcache_property, setitem, asyncthread

from . import MpvProcess

vd.theme_option('color_daw_header', 'underline', 'color of first line in a transcript section')
vd.theme_option('color_daw_playhead', 'blue', 'color of playhead line')
vd.theme_option('color_daw_cut', '238', 'color of cut rows')
vd.theme_option('daw_include_cuts', True, 'whether saving xmd format includes cuts with strikethrough')


TODO = '''
- split row at given time for 'a'
- getRowIndexByPlaytime: could use binary search
- rename 'marker' to 'section'
- skip cut segments while playing
  - play segments individually
  - colorize row based on time (do not change cursor)

- bug: Mikel and SaulL speakers?
- cut level (1=first pass, 2=second, etc)
- add undo to combining
- ) to reclose current row
- make sure round-tripping works
   - if we improve merge_transcript, can it reapply the word-level timings without screwing up the organization of the transcript?

## make markers for mag matter to delineate sections

- select to next marker
- move an edit time
- feature: play side sheet of rows
+ select some segments into side sheet and see what total duration they are
   - super neat if we can play them as an edit

- command to rollup whisper transcript by speaker again
- uncut command

5. basic editing
   - command to select rows from last marker (zs)
   - cleanup: rename row.word to row.text throughout

cleanups:
    - JSONDecodeError: sometimes query gets extra data with json.  make line buffering?

- sync gets lost if a word is <100ms +1
- changing speakers should set speaker on all baserows?
- highlight current word in transcript?

- change 'word' to 'text' throughout
- change 'baserows' to 'rows' throughout?  for parity in splitRow

- WEIRD: editing value on filter parms sheet updates value?!  how is it working?!
- WEIRD: agate with ratio=1 disables it?  what does ratio parm do?!

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
    'Return HH:MM:SS.s'
    if t is None:
        return ''
    if t < 0:
        return f'{t:0.1f}s'
    if t == 0:
        return ''
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t))*10)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:01d}'


def flatten_rows(rows):
    'Iterate through all baserows at the bottom of all rows.'
    for r in rows:
        if r.baserows:
            yield from flatten_rows(r.baserows)
        else:
            yield r


def replace_baserows(row):
    'Turn row into EditRow, recursively making its baserows also EditRows, until the bottom level which are simple AttrDicts.'
    row = AttrDict(row)
    if not row.baserows:
        return row

    r = EditRow(**row)
    r.subrows = [replace_baserows(baser) for baser in row.baserows]
    return r


@VisiData.api
def open_transcript(vd, p):
    '''path is transcript in JSON format; audio should be path.mp3'''
    vd.timeouts_before_idle = -1
    return PodcastEditingSheet(p.name, source=p)

@Column.api
def formatter_hhmmss(self, fmtstr):
    return to_hms

def _getter_duration(col, row):
    if row.cut:
        return 0

    uncutrows = [br for br in row.baserows if not br.cut]

    if not uncutrows:  # everything is cut
        return 0

    if len(uncutrows) == len(row.baserows):
        return row.end-row.start

    return sum(_getter_duration(col, br) for br in uncutrows)


class EditRow:
    def __init__(self, section:str='', speaker:str='', header:str='', **kwargs):
        self.section = section
        self.speaker = speaker
        self.header = header
        self.subrows = []

    def __contains__(self, t:float):
        if not self.start or not self.end:
            return False
        return self.start <= t <= self.end

    @drawcache_property
    def start(self) -> float:
        return min(r.end for r in self.uncutrows) if self.uncutrows else None

    @drawcache_property
    def end(self) -> float:
        return max(r.start for r in self.uncutrows) if self.uncutrows else None

    @drawcache_property
    def duration(self) -> float:
        return sum((r.duration or 0) for r in self.uncutrows) if self.uncutRows else 0

    @drawcache_property
    def text(self) -> str:
        if self.cut:
            # if shown directly, toplevel shows words for all rows regardless of cutness
            return ' '.join((r.word or '') for r in self.subrows)
        else:
            # otherwise cut subrows are elided
            return ' '.join((r.word or '') if not r.cut else '…' for r in self.uncutrows)

    @drawcache_property
    def uncutrows(self) -> list:
        return [r for r in self.subrows if not r.cut]

    @property
    def cut(self) -> int:
        return not bool(self.uncutrows)

    @drawcache_property
    def nwords(self) -> int:
        return sum(r.nwords if isinstance(r, EditRow) else 1 for r in self.subrows)

    def split_at_word(self, n:int) -> tuple['EditRow', 'EditRow']:
        wordnum = 0
        beforerows = []
        afterrows = []
        midrow = None
        for sr in self.uncutrows:
            nsubwords = len(sr.word.split())
            if wordnum < n:
                beforerows.append(sr)
            elif wordnum + nsubwords - 1 > n:
                afterrows.append(sr)
            else:
                midrow = sr
                cutwordnum = n - wordnum

            wordnum += nsubwords

        if midrow:  # word n is contained within this subrow
            if isinstance(midrow, EditRow):
                r1 = EditRow(section=midrow.section, speaker=midrow.speaker, header=midrow.header)
                r2 = EditRow(section=midrow.section, speaker=midrow.speaker)
                a, b = sr.split_at_word(cutwordnum)
                r1.subrows = beforerows + [a]
                r2.subrows = [b] + afterrows
                return r1, r2
            else:
                r1 = EditRow(section=midrow.section, speaker=midrow.speaker, header=midrow.header)
                r2 = EditRow(section=midrow.section, speaker=midrow.speaker)
                r1.subrows = beforerows + [midrow]
                r2.subrows = afterrows
                return r1, r2
        else:
            return None, None

    @property
    def baserows(self) -> list:  # deprecated
        return self.subrows

    @property
    def word(self) -> str:  # deprecated
        return self.text


class PodcastEditingSheet(Sheet):
    columns = [
        AttrColumn('section', width=20),
        AttrColumn('speaker'),
        AttrColumn('start', type=float, formatter='hhmmss'),
        AttrColumn('end', type=float, formatter='hhmmss'),
        Column('duration', type=float, formatter='hhmmss', cache=True, getter=_getter_duration),
        AttrColumn('cut', type=int, width=6),
        AttrColumn('score', type=float, width=0),
        AttrColumn('word', width=80),
        AttrColumn('baserows', type=vlen, width=0),
    ]
    colorizers = [
        RowColorizer(5, 'color_daw_header', lambda s,c,r,v: r.header),  # section header
        RowColorizer(5, 'color_daw_cut', lambda s,c,r,v: r.cut),
        RowColorizer(3, 'color_daw_playhead', lambda s,c,r,v: s.mpv.playback_time in r)
    ]
    nKeys = 2
    mpv = None
    nexthdrnum = 0

    curfilter = 'agate'
    curparm = 'ratio'

    def iterload(self):
        d = json.loads(self.source.open_text().read())
        self.speakers = defaultdict(list)  # speakername -> list of words/baserows
        sourceaudio = d.get('sourceaudio', None)
        if not sourceaudio:
            if self.source.with_suffix('.mp3').exists():
                sourceaudio = str(self.source.with_suffix('.mp3'))
            elif self.source.with_suffix('.wav').exists():
                sourceaudio = str(self.source.with_suffix('.wav'))

        if sourceaudio:
            self.mpv = MpvProcess(sourceaudio, self)
            self.mpv.start_mpv()
        else:
            vd.warning("no matching audio file")

        curhdr = ''
        try:
            for word in d['word_segments']:
                word['section'] = word.get('marker')
                if word.get('marker', curhdr) != curhdr:  # only the first row of a section has 'header'
                    curhdr = word['header'] = word['marker']

                self.speakers[word.get('speaker', None)].append(word)
                yield replace_baserows(word)
        except Exception as e:
            vd.exceptionCaught(e)

        self.cutlevel = max(r.cut if r.cut else 0 for r in self.rows)
        self.column('duration').aggregators = 'sum'
        self.column('start').aggregators = 'min'
        self.column('end').aggregators = 'max'

    def combine_rows(self, rows):
        uncutrows = [r for r in rows if not r.cut]
        newrow = AttrDict(word=' '.join(r.word for r in uncutrows),
                          speaker=' '.join(set(r.speaker for r in uncutrows if r.speaker)),
                          marker=rows[0].marker,
                          start=uncutrows[0].start if uncutrows else rows[0].start,
                          end=uncutrows[-1].end if uncutrows else rows[-1].end,
                          baserows=rows)
        self.addRow(newrow, index=self.cursorRowIndex)

        for r in rows:
            self.rows.remove(r)

    def expand_row(self, rowidx):
        baserows = self.rows[rowidx].baserows
        if baserows:
            if self.rows[rowidx].marker:
                baserows[0].marker = self.rows[rowidx].marker
            self.rows[rowidx:rowidx+1] = baserows
        else:
            vd.warning('no baserows')

    def cycle_speaker(self, row):
        speakers = list(self.speakers.keys())
        row.speaker = speakers[(speakers.index(row.speaker)+1)%len(speakers)]

    def getRowIndexByPlaytime(self, t:float, rows=None) -> int:
        try:
            return next(i for i,r in enumerate(rows or self.rows) if t in r)
        except StopIteration:
            vd.error(f'time {to_hms(t)} not found')

    def go_playhead(self):
        t = self.mpv.playback_time
        self.cursorRowIndex = self.getRowIndexByPlaytime(t)

    def add_marker(self):
        t = self.mpv.playback_time
        idx = self.getRowIndexByPlaytime(t)
        row = self.rows[idx]
        baseidx = self.getRowIndexByPlaytime(t, row.baserows)

        # create new row with second part
        newbaserows = row.baserows[baseidx:]
        newrow = AttrDict(word=' '.join(r.word for r in flatten_rows(newbaserows)),
                          speaker=row.speaker,
                          start=row.baserows[baseidx].start,
                          end=row.end,
                          baserows=newbaserows)

        if t > newrow.start:
            vd.status(f'cut {int((t-newrow.start)*1000)}ms after start of "{newrow.word[:7]}"')

        # fix old row with first part
        row.end = row.baserows[baseidx-1].end
        row.baserows = row.baserows[:baseidx]
        row.word = ' '.join(r.word for r in flatten_rows(row.baserows))

        # XXX: should this be actual mark time or squarely between split words?
        markertime = t  # (newrow.start + row.end)/2
        self.addRow(AttrDict(word='', header=str(self.nextheadernum), start=markertime, end=markertime, baserows=[]), index=idx+1)
        self.addRow(newrow, index=idx+2)

    @property
    def nexthdrnum(self):
        n = self.nexthdrnum
        self.nexthdrnum += 1
        return n

    def go_header_next(self, didx:int, startrow:int):
        i = startrow
        while 0 <= i < self.nRows-(0 if didx < 0 else 1):
            i += didx
            if self.rows[i].header:
                self.cursorRowIndex = i
                return
        vd.fail("no marker")

    @asyncthread
    def cut_rows(self, rows):
        for row in rows:
            row['cut'] = self.cutlevel

    @property
    def playheadStatus(self):
        try:
            return to_hms(self.mpv.playback_time)
        except Exception as e:
            if vd.options.debug:
                vd.exceptionCaught(e)

    def checkCursor(self):
        return super().checkCursor()
        # disable sync if paused or not top sheet
        if self.mpv and not self.mpv.paused:
            if self is vd.sheets[0] and \
                self.cursorRowIndex < self.nRows-1:
                    nextrow = self.rows[self.cursorRowIndex+1]
                    if nextrow.start <= self.mpv.playback_time <= nextrow.end:
                        self.cursorRowIndex += 1

            skipped_cuts = False

            while self.rows[self.cursorRowIndex].cut:
                self.cursorRowIndex += 1
                skipped_cuts = True

            if skipped_cuts:
                self.mpv.play_audio(self.rows[self.cursorRowIndex])

        super().checkCursor()

    def input_afilter_parm(self):
        def _fmt_afilter_parm(match, row, trigger_key):
            return f'{row.key} - {row.desc}'

        return vd.activeSheet.inputPalette('choose your filter parameter: ',
                self.mpv.afilters[self.curfilter],
                value_key='key',
                formatter=_fmt_afilter_parm,
#                help=vd.help_join,
                type='afilter')

    def setFilterParmByIndex(self, filtername, parmname, idxvalue):
        self.mpv.set_filter_parm(filtername, parmname, self.mpv.afilter_options[filtername][parmname][idxvalue])

    def reformat_row(self, rowidx):
        row = self.rows[rowidx]

        formatted_rows = []
        wordnum = 0
        for line in textwrap.wrap(row.word,
                        width=self.column('word').width-2,
                        break_long_words=False,
                        break_on_hyphens=False):
            pr, row = row.split_at_word(len(line.split())-1)
            if pr:
                formatted_rows.append(pr)
            if not row:
                break

        self.rows[rowidx:rowidx+1] = formatted_rows

    def reformat_rows(self, rows):
        for row in rows:
            if not row.cut:
                self.reformat_row(rows.index(row))

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
                    fp.write(f'{i}. cut from {to_hms(cut_start.start)} to {to_hms(cut_end.end)}: {cut_start.word[:10]}...{cut_end.word[-10:]}\n')
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

            if row.get('marker', prevhdr) != prevhdr:
                prevhdr = row.get('marker')
                fp.write(f'## {prevhdr}\n\n')

            line = f'[{timestr}] {row.speaker}: {row.word}'
            line = line.strip()
            if row.cut:
                if sheet.options.daw_include_cuts:
                    line = f'~~{line}~~'
                else:
                    line = ''

            if line:
                fp.write(line+'\n\n')

@VisiData.api
def save_transcript(vd, p, sheet):
    d = dict(word_segments=sheet.rows, sourceaudio=sheet.mpv.sourceaudio)
    with p.open(mode='w', encoding='utf-8') as fp:
        fp.write(json.dumps(d)+'\n')

PodcastEditingSheet.options.save_filetype = 'transcript'
PodcastEditingSheet.options.disp_rstatus_fmt = '{sheet.playheadStatus}  ' + Sheet.options.disp_rstatus_fmt

PodcastEditingSheet.addCommand('P', 'play-row', 'mpv.play_audio(cursorRow)')
PodcastEditingSheet.addCommand('p', 'play-toggle', 'mpv.audio_pause(not mpv.paused)')
FilterParametersSheet.addCommand('P', 'play-toggle', 'source.mpv.audio_pause(not source.mpv.paused)')
PodcastEditingSheet.addCommand('g)', 'combine-selected', 'combine_rows(selectedRows)')
PodcastEditingSheet.addCommand('(', 'expand-row', 'expand_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('g(', 'expand-selected', 'for row in selectedRows: expand_row(rows.index(row))')

PodcastEditingSheet.addCommand('Ctrl+R', 'restart-mpv', 'mpv.start_mpv()')

FilterParametersSheet.addCommand('a', 'add-filter', 'source.mpv.add_filter()', 'add filter on current row')
FilterParametersSheet.addCommand('d', 'remove-filter', 'source.mpv.remove_filter()', 'remove filter on current row')


for i in range(0, 10):
    PodcastEditingSheet.addCommand(str(i), f'set-afilter-parm-{i}', f'setFilterParmByIndex(curfilter, curparm, {i})')
    FilterParametersSheet.addCommand(str(i), f'set-afilter-parm-{i}', f'source.setFilterParmByIndex(cursorRow.filter, cursorRow.filter_parm, {i}); reload()')

PodcastEditingSheet.addCommand('zf', 'choose-afilter-parm', 'sheet.curparm = input_afilter_parm()', '')

PodcastEditingSheet.addCommand('', 'cycle-speaker', 'cycle_speaker(cursorRow)')
PodcastEditingSheet.addCommand('[', 'audio-back-10', 'mpv.seek_audio(-10); go_playhead()')
PodcastEditingSheet.addCommand(']', 'audio-forward-10', 'mpv.seek_audio(+10); go_playhead()')
PodcastEditingSheet.addCommand('g[', 'audio-back-60', 'mpv.seek_audio(-60); go_playhead()')
PodcastEditingSheet.addCommand('g]', 'audio-forward-60', 'mpv.seek_audio(+60); go_playhead()')
PodcastEditingSheet.addCommand('gg', 'go-playhead', 'go_playhead()', 'move row cursor to playhead' )

PodcastEditingSheet.addCommand('a', 'add-marker', 'add_marker(); cursorDown(2)', 'add marker at current playhead, splitting if necessary')
PodcastEditingSheet.addCommand('d', 'cut-row', 'cut_rows([cursorRow]); cursorDown(1)', 'cut audio for line at cursor row')
PodcastEditingSheet.addCommand('gd', 'cut-selected', 'cut_rows(selectedRows)', 'cut audio for selected rows')
PodcastEditingSheet.addCommand('<', 'go-marker-prev', 'go_header_next(-1, cursorRowIndex)', 'move row cursor to previous marker')
PodcastEditingSheet.addCommand('>', 'go-marker-next', 'go_header_next(+1, cursorRowIndex)', 'move row cursor to next marker')
PodcastEditingSheet.addCommand('g<', 'go-marker-first', 'go_header_next(+1, 0)', 'move row cursor to first marker')
PodcastEditingSheet.addCommand('g>', 'go-marker-last', 'go_header_next(-1, nRows-1)', 'move row cursor to last marker')

PodcastEditingSheet.addCommand('f', 'open-vdaw-filters', 'vd.push(FilterParametersSheet("filters", source=sheet))')
PodcastEditingSheet.addCommand('r', 'reformat-row', 'reformat_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('gr', 'reformat-selected', 'reformat_rows(selectedRows)')
