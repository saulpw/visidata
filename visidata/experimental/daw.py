import socket
import json

from visidata import VisiData, Sheet, ItemColumn, asyncthread, AttrDict

# - launch mpv process with audio from transcript
# - save transcript as .md with strikethroughs
# - save punchlist for edits

@VisiData.api
def open_transcript(vd, p):
    '''path is transcript in JSON format; audio should be path.mp3'''
    return PodcastEditingSheet(p.name, source=p)


class PodcastEditingSheet(Sheet):
    columns = [
        ItemColumn('start', type=float),
        ItemColumn('end', type=float),
        ItemColumn('speaker'),
        ItemColumn('word'),
        ItemColumn('score', type=float),
    ]

    def iterload(self):
        d = json.loads(self.source.open_text().read())
        for word in d['word_segments']:
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


PodcastEditingSheet.addCommand('1', 'audio-pause', 'audio_pause(True)')
PodcastEditingSheet.addCommand('2', 'play-row', 'play_audio(cursorRow)')
