from collections import defaultdict

import json
import copy
import time
import os
import os.path
import socket
import subprocess

from visidata import vd, VisiData, Sheet, ItemColumn, asyncthread, AttrDict, vlen, RowColorizer, setitem, Column

vd.theme_option('color_daw_marker', 'white on blue', 'color of marker rows in the DAW')
vd.theme_option('color_daw_cut', '238', 'color of cut rows')
vd.theme_option('daw_include_cuts', True, 'whether saving xmd format includes cuts with strikethrough')
vd.option('daw_mpv_cmd', '/usr/bin/mpv --no-terminal --ao=pulse', '')


TODO = '''
+ add default aggregator for duration
- add undo to combining
- ) to reclose current row
- skip cut segments while playing
- make sure round-tripping works
   - if we improve merge_transcript, can it reapply the word-level timings without screwing up the organization of the transcript?
- section should be set for every segment
- header only emitted for the first one

## make markers for mag matter to delineate sections

+ add marker to current row (just edit using vd commands)
- split row at given time, maintaining structure
- duration of each segment
- aggregate time for each section
- select to next marker
- move an edit time
- select some segments into side sheet and see what total duration they are
   - super neat if we can play them as an edit

- command to rollup whisper transcript by speaker again
- uncut command

5. basic editing
   - command to select rows from last marker (zs)
   - cleanup: rename row.word to row.text throughout
   - r to reformat current row.text into multiple rows, split at column width
   - gr to reformat all selected rows
   - p to play/pause, Shift+P to play from cursor



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
    'Turn row into AttrDict, recursively making its baserows also AttrDicts.'
    r = AttrDict(row)
    r.baserows = [replace_baserows(baser) for baser in (r.baserows or [])]
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


class PodcastEditingSheet(Sheet):
    columns = [
        ItemColumn('marker'),
        ItemColumn('speaker'),
        ItemColumn('start', type=float, formatter='hhmmss'),
        ItemColumn('end', type=float, formatter='hhmmss'),
        Column('duration', type=float, formatter='hhmmss', cache=True, getter=_getter_duration),
        ItemColumn('cut', width=6),
        #ItemColumn('start', type=float),
        #ItemColumn('end', type=float),
        ItemColumn('score', type=float, width=0),
        ItemColumn('word', width=80),
        ItemColumn('baserows', type=vlen, width=0),
    ]
    colorizers = [
        RowColorizer(5, 'color_daw_marker', lambda s,c,r,v: r.marker),
        RowColorizer(5, 'color_daw_cut', lambda s,c,r,v: r.cut)
    ]
    nKeys = 3
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

        try:
            for word in d['word_segments']:
                self.speakers[word.get('speaker', None)].append(word)
                yield replace_baserows(word)
        except Exception as e:
            vd.exceptionCaught(e)

        self.column('duration').aggregators = 'sum'

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
        for i, r in enumerate(rows or self.rows):
            if t <= r.end:  # when playhead is before line end for the first time
                return i

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

    def go_marker_next(self, didx:int, startrow:int):
        i = startrow
        while 0 <= i < self.nRows-(0 if didx < 0 else 1):
            i += didx
            if self.rows[i].marker:
                self.cursorRowIndex = i
                return
        vd.fail("no marker")

    @asyncthread
    def cut_rows(self, rows):
        for row in rows:
            row['cut'] = True

    @property
    def playheadStatus(self):
        try:
            return to_hms(self.mpv.playback_time)
        except Exception as e:
            if vd.options.debug:
                vd.exceptionCaught(e)

    def checkCursor(self):
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


class MpvProcess:
    mpvproc = None

    afilters = dict(
        agate=[AttrDict(key=k, desc=desc) for k, desc in dict(
            level_in='input level before filtering',
            mode='upward=higher parts amplified; downward=lower parts reduced',
            range='level of gain reduction when the signal is below the threshold',
            threshold='If a signal rises above this level the gain reduction is released',
            ratio='ratio by which the signal is reduced',
            attack='milliseconds the signal has to rise above the threshold before gain reduction stops',
            release='milliseconds the signal has to fall below the threshold before the reduction is increased again',
            makeup='amount of amplification of signal after processing',
            knee='Curve the sharp knee around the threshold to enter gain reduction more softly',
            detection='if exact signal should be taken for detection or an RMS like one',
            link='if the average level between all channels or the louder channel affects the reduction'
         ).items()],
        loudnorm=[AttrDict(key=k, desc=desc) for k, desc in dict(
           i='integrated loudness target',
           lra='loudness range target',
           tp='maximum true peak',
           measured_i='Measured IL of input file',
           measured_lra='Measured LRA of input file',
           measured_tp='Measured true peak of input file',
           measured_thresh='Measured threshold of input file',
           offset='offset gain. Gain is applied before the true-peak limiter',
           linear='Normalize by linearly scaling the source audio',
           dual_mono='Treat mono input files as "dual-mono"',
         ).items()])
    # possible values across buttons 0 (default) to 9
    afilter_options = dict(agate=dict(
                                level_in=[1, 0.015625, 0.03, 0.1, 0.3, 1, 3, 10, 30, 64],
                                mode=['downward', 'upward'],
                                range=[0.06125,.1,.2,.3,.4,.5,.6,.7,.8,.9],
                                threshold=[0.125,.1,.2,.3,.4,.5,.6,.7,.8,.9],
                                ratio=[2,1,3,10,30,100,300,1000,3000,9000],
                                attack=[20, 0.01, .1, 1, 3, 10, 30, 100, 1000, 9000],
                                release=[250, 0.01, .1, 1, 3, 10, 30, 100, 1000, 9000],
                                makeup=[1,1,2,3,4,6,8,16,32,64],
                                knee=[2.828427,1,2,2.8,3,4,5,6,7,8],
                                detection=['rms', 'peak'],
                                link=['average', 'maximum']),
                           loudnorm=dict(
                               i=[-24.0],
                               lra=[7.0],
                               tp=[-0.0],
                               measured_i=[None],
                               measured_lra=[None],
                               measured_tp=[None],
                               measured_thresh=[None],
                               offset=[0, -99,-50,-20,-5,5,20,50,99],
                               linear=[True, False],
                               dual_mono=[False, True],
                           ))
    afilter_parms = {}

    def __init__(self, sourcefn, source:Sheet):
        self.sourceaudio = sourcefn
        self.mpvproc = None
        self.source = source

    def add_filter(self, filtername):
        self.afilter_parms[filtername] = {
            parmname:values[0] for parmname, values in self.afilter_options[filtername].items()
        }
        vd.status(f'filter {filtername} added')

    def remove_filter(self, filtername):
        del self.afilter_parms[filtername]

    def set_filter_parm(self, filtername, parmname, val):
        if filtername not in self.afilter_parms:
            self.add_filter(filtername)
        self.afilter_parms[filtername][parmname] = val
        self.restart_mpv(self.source.cursorRow.start) # self.playback_time

    @property
    def mpvsockfn(self):
        return '/tmp/vdmpv'

    def restart_mpv(self, t:float):
        self.start_mpv()
        time.sleep(0.5)
        self.seek_audio(t, 'absolute')
        self.audio_pause(False)

    def is_default(self, filtername, parmname, val):
        return val is None or val == self.afilter_options[filtername][parmname][0]

    def start_mpv(self):
        if self.mpvproc:
            self.mpv_command(command=["quit"])
            self.mpvproc = None

        if os.path.exists(self.mpvsockfn):
            os.unlink(self.mpvsockfn)

        if not os.path.exists(self.mpvsockfn):
            if not os.path.exists(self.sourceaudio):
                vd.warning(f'{self.sourceaudio} does not exist')
                return

            filterparams = ','.join(
                    (f'{filtername}=' + ':'.join(f'{k}={v}' for k, v in filterparms.items() if not self.is_default(filtername, k, v)))
                        for filtername, filterparms in self.afilter_parms.items())

            if filterparams:
                filterparams = '--af='+filterparams
                vd.status(filterparams)

            self.mpvproc = subprocess.Popen(f'{vd.options.daw_mpv_cmd} --input-ipc-server={self.mpvsockfn} {filterparams} {self.sourceaudio}', shell=True)

    def mpv_command(self, **kwargs):
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(self.mpvsockfn)
        sock.sendall(json.dumps(kwargs).encode() + b'\n')
        sock.close()

    def mpv_query(self, propname):
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(self.mpvsockfn)
        sock.sendall(json.dumps(dict(command=['get_property', propname])).encode() + b'\n')
        r = sock.recv(4096)
        d = json.loads(r)
        if d.get('error', None) != 'success':
            vd.error(d)

        sock.close()
        return d['data']

    def audio_pause(self, b=True):
        self.mpv_command(command=['set_property', 'pause', b])

    @property
    def paused(self):
        p = self.mpv_query('pause')
#        vd.status(f'paused={p}')
        return p

    @property
    def playback_time(self):
        return float(self.mpv_query('playback-time'))

    def play_audio(self, row):
        self.seek_audio(row.start, 'absolute')
        self.audio_pause(False)

    def seek_audio(self, dt:float, *args):
        self.mpv_command(command=['seek', str(dt), *args])

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

    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        for row in sheet.rows:
#            timestr = f'{row.start:0.1f}'
            timestr = to_hms(row.start)

            if row.marker:
                fp.write('## {row.marker}\n\n')

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
PodcastEditingSheet.addCommand('g)', 'combine-selected', 'combine_rows(selectedRows)')
PodcastEditingSheet.addCommand('(', 'expand-row', 'expand_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('g(', 'expand-selected', 'for row in selectedRows: expand_row(rows.index(row))')

PodcastEditingSheet.addCommand('Ctrl+R', 'restart-mpv', 'mpv.start_mpv()')

FilterParametersSheet.addCommand('P', 'audio-pause', 'source.mpv.audio_pause(True)')
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
PodcastEditingSheet.addCommand('d', 'cut-rows', 'cut_rows([cursorRow]); cursorDown(1)', 'cut audio for line at cursor row')
PodcastEditingSheet.addCommand('gd', 'cut-selected', 'cut_rows(selectedRows)', 'cut audio for selected rows')
PodcastEditingSheet.addCommand('<', 'go-marker-prev', 'go_marker_next(-1, cursorRowIndex)', 'move row cursor to previous marker')
PodcastEditingSheet.addCommand('>', 'go-marker-next', 'go_marker_next(+1, cursorRowIndex)', 'move row cursor to next marker')
PodcastEditingSheet.addCommand('g<', 'go-marker-first', 'go_marker_next(+1, 0)', 'move row cursor to first marker')
PodcastEditingSheet.addCommand('g>', 'go-marker-last', 'go_marker_next(-1, nRows-1)', 'move row cursor to last marker')

PodcastEditingSheet.addCommand('f', 'open-vdaw-filters', 'vd.push(FilterParametersSheet("filters", source=sheet))')
