import json
from pathlib import Path

import pytest

import visidata
from visidata import vd

MINI = Path(__file__).parent / 'mini.transcript'


@pytest.fixture
def daw(monkeypatch):
    'Import the experimental daw module with mpv subprocess startup stubbed out.'
    import visidata.experimental.daw.vdaw as vdaw
    monkeypatch.setattr(vdaw.MpvProcess, 'start_mpv', lambda *_: None)
    return vdaw


@pytest.fixture
def minisheet(daw):
    'PodcastEditingSheet loaded synchronously from the mini.transcript fixture.'
    sheet = daw.open_transcript(vd, visidata.Path(str(MINI)))
    sheet.reload.__wrapped__(sheet)  # synchronous; no asyncthread
    vd.sync()
    return sheet


def test_bulk_combine_groups_by_speaker(minisheet):
    'bulk-combine collapses consecutive same-speaker rows into one row each.'
    assert len(minisheet.rows) == 4

    minisheet.bulk_combine(minisheet.rows)

    assert [r.speaker for r in minisheet.rows] == ['Alice', 'Bob']
    assert minisheet.rows[0].text == 'Hello world'
    assert minisheet.rows[1].text == 'Hi there'


def test_bulk_combine_save_preserves_sourceaudio(daw, minisheet, tmp_path):
    'Saving after bulk-combine must keep the top-level sourceaudio key.'
    assert minisheet.sourceaudio == 'mini.mp3'

    minisheet.bulk_combine(minisheet.rows)

    out = visidata.Path(str(tmp_path / 'out.transcript'))
    daw.save_transcript(vd, out, minisheet)
    vd.sync()

    saved = json.loads(out.open_text().read())
    assert saved['sourceaudio'] == 'mini.mp3'


def test_discovered_audio_overrides_missing_sourceaudio(daw, tmp_path):
    'A sibling .mp3 with the same stem wins when the recorded sourceaudio file is missing.'
    src = tmp_path / 'show.transcript'
    sibling = tmp_path / 'show.mp3'
    sibling.write_bytes(b'')
    src.write_text(json.dumps({'word_segments': [
        {'section': '', 'speaker': 'Alice', 'start': 1.0, 'end': 1.5, 'cut': None, 'subrows': [], 'text': 'Hello'},
    ], 'sourceaudio': 'gone/missing.mp3'}))

    sheet = daw.open_transcript(vd, visidata.Path(str(src)))
    sheet.reload.__wrapped__(sheet)
    vd.sync()

    assert sheet.sourceaudio == str(sibling)
