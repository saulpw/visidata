import socket
import json
from collections import defaultdict

from visidata import VisiData, Sheet, ItemColumn, asyncthread, AttrDict

TODO = '''
2. save transcript as .md
   + command to combine selected rows into runs by speaker
   + reexpand combined row
   + change current row speaker, cycle through speakers
   ? edit text (is current vd edit sufficient?)

3. playback movement
   - show current playback timestamp on status line
   - [ / ] to play backward/forward 10s (z[ for 1s, g[ for 1 minute)
     - sort still accessible via longname
   - launch mpv process with audio from transcript

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
    ]
    nKeys = 1

    def iterload(self):
        d = json.loads(self.source.open_text().read())
        self.speakers = defaultdict(list)  # speakername -> list of words/baserows
        for word in d['word_segments']:
            self.speakers[word['speaker']].append(word)
            yield AttrDict(word)

    def mpv_command(self, **kwargs):
        sock = socket.socket(socket.AF_UNIX)
        sock.connect('/tmp/mpv')
        sock.sendall(json.dumps(kwargs).encode() + b'\n')
        sock.close()

    def audio_pause(self, b=True):
        self.mpv_command(command=['set_property', 'pause', b])

    def play_audio(self, row):
        self.mpv_command(command=['seek', str(row.start), 'absolute'])
        self.audio_pause(False)

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
        self.rows[rowidx:rowidx+1] = self.rows[rowidx].baserows

    def cycle_speaker(self, row):
        speakers = list(self.speakers.keys())
        row.speaker = speakers[(speakers.index(row.speaker)+1)%len(speakers)]


@VisiData.api
def save_xmd(vd, p, sheet):
    assert isinstance(sheet, PodcastEditingSheet)

    with p.open(mode='w', encoding=sheet.options.save_encoding) as fp:
        for row in sheet.rows:
            fp.write(f'[{row.start:0.1f}] {row.speaker}: {row.word}\n\n')


PodcastEditingSheet.addCommand('1', 'audio-pause', 'audio_pause(True)')
PodcastEditingSheet.addCommand('2', 'play-row', 'play_audio(cursorRow)')
PodcastEditingSheet.addCommand('3', 'combine-selected', 'combine_rows(selectedRows)')
PodcastEditingSheet.addCommand('4', 'expand-row', 'expand_row(cursorRowIndex)')
PodcastEditingSheet.addCommand('5', 'cycle-speaker', 'cycle_speaker(cursorRow)')
