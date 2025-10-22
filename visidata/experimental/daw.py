from collections import defaultdict

import json
import os
import os.path
import socket
import subprocess

from visidata import vd, VisiData, Sheet, ItemColumn, asyncthread, AttrDict, vlen


TODO = '''
- undo combining
- changing speakers should set speaker on all baserows?
- keep playhead and row cursor in sync?
- highlight current word in transcript?
- visidata multiline for all lines at once

3. playback movement
   + launch mpv process with audio from transcript
   + show current playback timestamp on status line
   + [ / ] to play backward/forward 10s (z[ for 1s, g[ for 1 minute)
     - sort still accessible via longname

4. add marker
   - 'a' to add marker at current timestamp
      - may split row (with name or note inserted between)
   - < / > to start playback at previous/next marker (g< to first marker, g> to last marker)
   - colorize marker rows

5. basic editing
   - add edit column
   - command to mark selected rows as 'cut'
   - command to select rows from last marker
   - colorize cut rows
   - save .md with with markdown ~~strikethrough~~ for cut sections
   - save back as same json with marker annotations and cut column
      - should be round-trippable
   - save text punchlist for edits

5. numbered markers?
   - 1-9 for numbered (temporary) marker
   - 'z1' to set marker 1 at current timestamp; '1' to play starting at marker 1

6. playback should skip cut sections
'''

@VisiData.api
def open_transcript(vd, p):
    '''path is transcript in JSON format; audio should be path.mp3'''
    return PodcastEditingSheet(p.name, source=p)


class PodcastEditingSheet(Sheet):
    columns = [
        ItemColumn('speaker'),
        ItemColumn('start', type=float),
        ItemColumn('end', type=float),
        ItemColumn('score', type=float, width=0),
        ItemColumn('word', width=80),
        ItemColumn('baserows', type=vlen, width=0),
    ]
    nKeys = 1

    @property
    def mpvsockfn(self):
        return '/tmp/vdmpv'

    def iterload(self):
        d = json.loads(self.source.open_text().read())
        self.speakers = defaultdict(list)  # speakername -> list of words/baserows
        self.sourceaudio = d.get('sourceaudio', None) or str(self.source.with_suffix('.mp3'))
        self.start_mpv()

        for word in d['word_segments']:
            self.speakers[word['speaker']].append(word)
            yield AttrDict(word)

    def start_mpv(self):
        if os.path.exists(self.mpvsockfn):
            os.unlink(self.mpvsockfn)

        if not os.path.exists(self.mpvsockfn):
            if not os.path.exists(self.sourceaudio):
                vd.warning(f'{self.sourceaudio} does not exist')
                return

            p = subprocess.Popen(f'/usr/bin/mpv --input-ipc-server={self.mpvsockfn} {self.sourceaudio} --no-terminal', shell=True)

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
        if d['error'] != 'success':
            vd.error(d)

        sock.close()
        return d['data']

    def audio_pause(self, b=True):
        self.mpv_command(command=['set_property', 'pause', b])

    def play_audio(self, row):
        self.seek_audio(row.start, 'absolute')
        self.audio_pause(False)

    def seek_audio(self, dt:float, *args):
        self.mpv_command(command=['seek', str(dt), *args])

    def combine_rows(self, rows):
        newrow = None
        for r in list(rows):
            if not newrow or newrow.speaker != r.speaker:
                newrow = AttrDict(word='', speaker=r.speaker, start=r.start, end=0, baserows=[])
                self.addRow(newrow)

            newrow.word += r.word + ' '
            newrow.end = r.end
            newrow.baserows.extend(r.baserows or [r])
            self.rows.remove(r)

    def expand_row(self, rowidx):
        self.rows[rowidx:rowidx+1] = [AttrDict(r) for r in self.rows[rowidx].baserows]

    def cycle_speaker(self, row):
        speakers = list(self.speakers.keys())
        row.speaker = speakers[(speakers.index(row.speaker)+1)%len(speakers)]

    @property
    def playheadStatus(self):
        try:
            return to_hms(float(self.mpv_query('playback-time')))
        except Exception as e:
            vd.exceptionCaught(e)

def to_hms(t:float) -> str:
    'Return HH:MM:SS.s'
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t))*10)
    return f'{h:02d}:{m:02d}:{s:02d}.{ms:01d}'

@VisiData.api
def save_xmd(vd, p, sheet):
    assert isinstance(sheet, PodcastEditingSheet)

    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        for row in sheet.rows:
            fp.write(f'[{row.start:0.1f}] {row.speaker}: {row.word}\n\n')

@VisiData.api
def save_transcript(vd, p, sheet):
    with p.open(mode='w', encoding='utf-8') as fp:
        d = dict(word_segments=sheet.rows, sourceaudio=self.sourceaudio)
        fp.write(json.dumps(d)+'\n')

PodcastEditingSheet.options.save_filetype = 'transcript'
PodcastEditingSheet.options.disp_rstatus_fmt = '{sheet.playheadStatus}  ' + Sheet.options.disp_rstatus_fmt

PodcastEditingSheet.addCommand('1', 'play-row', 'play_audio(cursorRow)')
PodcastEditingSheet.addCommand('2', 'audio-pause', 'audio_pause(True)')
PodcastEditingSheet.addCommand('3', 'combine-selected', 'combine_rows(selectedRows)')
PodcastEditingSheet.addCommand('4', 'expand-row', 'expand_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('g4', 'expand-selected', 'for row in selectedRows: expand_row(rows.index(row))')
PodcastEditingSheet.addCommand('5', 'cycle-speaker', 'cycle_speaker(cursorRow)')
PodcastEditingSheet.addCommand('[', 'audio-back-10', 'seek_audio(-10)')
PodcastEditingSheet.addCommand(']', 'audio-forward-10', 'seek_audio(+10)')
PodcastEditingSheet.addCommand('g[', 'audio-back-60', 'seek_audio(-60)')
PodcastEditingSheet.addCommand('g]', 'audio-forward-60', 'seek_audio(+60)')
