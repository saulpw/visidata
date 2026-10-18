import json
import threading
from types import SimpleNamespace

import pytest

import visidata
from visidata import vd, ItemColumn
from visidata.errors import ExpectedException
import visidata.experimental.llm


class FakeMessages:
    def __init__(self, texts):
        self.texts = list(texts)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        text = self.texts.pop(0)
        if isinstance(text, Exception):
            raise text
        return SimpleNamespace(
            stop_reason='end_turn',
            content=[SimpleNamespace(type='thinking', thinking=''),
                     SimpleNamespace(type='text', text=text)],
            usage=SimpleNamespace(input_tokens=10, output_tokens=5))


@pytest.fixture
def fake(monkeypatch):
    msgs = FakeMessages([])
    monkeypatch.setattr(vd, '_anthropic_client', SimpleNamespace(beta=SimpleNamespace(messages=msgs)), raising=False)
    yield msgs
    vd._anthropic_client = None


def textsheet(*texts):
    sheet = visidata.Sheet('llmtest', columns=[ItemColumn('text', 0)], rows=[[t] for t in texts])
    sheet.ensureLoaded()
    return sheet


def analyze(sheet, query='q?'):
    col = sheet.column('text')
    sheet.llmAnalyzeColumn(col, sheet.rows, query)
    vd.sync()
    return {c.name: [c.getValue(r) for r in sheet.rows] for c in sheet.columns}


@pytest.mark.usefixtures('curses_setup')
class TestLLM:
    def test_results(self, fake):
        fake.texts = [json.dumps({'score': 0.75, 'analysis': 'yes'})]
        cols = analyze(textsheet('hello', ''))
        assert cols['text_llm_score'] == [0.75, None]
        assert cols['text_llm_analysis'] == ['yes', None]
        assert cols['text_llm_tokens'] == [15, None]
        assert len(fake.calls) == 1

    def test_request(self, fake):
        fake.texts = ['{"score": 1, "analysis": ""}']
        analyze(textsheet('hello'))
        kw = fake.calls[0]
        assert kw['model'] == 'claude-opus-5-5'
        assert 'temperature' not in kw
        assert kw['output_config']['format']['type'] == 'json_schema'

    def test_fenced_json(self, fake):
        fake.texts = ['```json\n{"score": 0.5, "analysis": "fenced"}\n```']
        cols = analyze(textsheet('hello'))
        assert cols['text_llm_score'] == [0.5]
        assert cols['text_llm_analysis'] == ['fenced']

    def test_long_cell_sent_whole(self, fake):
        fake.texts = ['{"score": 1, "analysis": ""}']
        longtext = 'x' * 100000
        analyze(textsheet(longtext))
        assert longtext in fake.calls[0]['messages'][0]['content']

    def test_api_error_row(self, fake):
        fake.texts = [RuntimeError('boom'), '{"score": 1, "analysis": "ok"}']
        cols = analyze(textsheet('a', 'b'))
        assert cols['text_llm_analysis'] == ['Error: boom', 'ok']

    def test_missing_key_fails_before_thread(self, monkeypatch):
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        vd._anthropic_client = None
        sheet = textsheet('a')
        with pytest.raises(ExpectedException, match='ANTHROPIC_API_KEY'):
            sheet.llmAnalyzeColumn(sheet.column('text'), sheet.rows, 'q?')
        assert len(sheet.columns) == 1

    def test_confirm_in_main_thread(self, fake, monkeypatch):
        confirmed = []
        monkeypatch.setattr(vd, 'confirm', lambda prompt, *a, **kw: confirmed.append(threading.current_thread()), raising=False)
        fake.texts = ['{"score": 1, "analysis": ""}'] * 101
        vd.options.llm_rate_delay = 0
        analyze(textsheet(*['a']*101))
        assert confirmed == [threading.current_thread()]

    def test_query_rows(self, fake, monkeypatch):
        pushed = []
        monkeypatch.setattr(vd, 'push', lambda vs, *a, **kw: pushed.append(vs), raising=False)
        fake.texts = ['line one\nline two']
        sheet = textsheet('alpha', 'beta')
        sheet.llmQueryRows(sheet.rows, 'what is common?')
        vd.sync()
        assert len(fake.calls) == 1
        kw = fake.calls[0]
        assert 'output_config' not in kw
        prompt = kw['messages'][0]['content']
        assert 'what is common?' in prompt
        assert json.dumps([{'text': 'alpha'}, {'text': 'beta'}]) in prompt
        vs = pushed[0]
        vs.ensureLoaded()
        assert [r[1] for r in vs.rows] == ['line one', 'line two']
