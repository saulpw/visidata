import stat

import pytest

from visidata import vd


# rowdef: n/a — exercises the $EDITOR launch+readback path that Ctrl+O uses
# during cell editing (visidata/_input.py: `edit_v = vd.launchExternalEditor(v)`)
# and that DirSheet sysopen-row uses. A non-interactive $EDITOR script stands in
# for the human, so the launch/readback is assertable headlessly (manual-tests.md #18).
class TestLaunchEditor:
    def _editor(self, tmp_path, body):
        'Write an executable $EDITOR script whose body acts on "$1" (the temp file).'
        p = tmp_path / 'fakeeditor.sh'
        p.write_text('#!/bin/sh\n' + body + '\n')
        p.chmod(p.stat().st_mode | stat.S_IXUSR)
        return str(p)

    def test_readback(self, tmp_path, monkeypatch):
        # editor rewrites the file; launchExternalEditor returns the new contents
        monkeypatch.setenv('EDITOR', self._editor(tmp_path, 'printf EDITED-"$(cat "$1")" > "$1"'))
        assert vd.launchExternalEditor('hello') == 'EDITED-hello'

    def test_trailing_newlines_trimmed(self, tmp_path, monkeypatch):
        # the function rstrips inevitable trailing newlines a real editor adds
        monkeypatch.setenv('EDITOR', self._editor(tmp_path, 'printf "one\\ntwo\\n\\n" > "$1"'))
        assert vd.launchExternalEditor('x') == 'one\ntwo'

    def test_unchanged_roundtrips(self, tmp_path, monkeypatch):
        # editor that leaves the file alone returns the original value
        monkeypatch.setenv('EDITOR', self._editor(tmp_path, ':'))
        assert vd.launchExternalEditor('keepme') == 'keepme'

    def test_no_editor_fails(self, monkeypatch):
        monkeypatch.delenv('EDITOR', raising=False)
        monkeypatch.delenv('VISUAL', raising=False)
        with pytest.raises(Exception):
            vd.launchExternalEditor('hello')
