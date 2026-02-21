'''
Browse Claude Code's ~/.claude directory.

    vd ~/.claude
    vd ~/.claude -f claude

Top-level shows projects, history, settings, etc.
Opening a project shows sessions.
Opening a session shows the conversation messages.
'''

import json
from datetime import datetime, timezone

from visidata import vd, VisiData, Sheet, Column, Path, date, AttrDict


def _ts(s):
    'Parse ISO timestamp or epoch-ms into datetime.'
    if not s:
        return None
    if isinstance(s, (int, float)):
        return datetime.fromtimestamp(s / 1000, tz=timezone.utc)
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00'))
    except Exception:
        return None


def _content_text(msg):
    'Extract display text from a message content field.'
    c = msg.get('content', '') if isinstance(msg, dict) else ''
    if isinstance(c, str):
        return c.strip()
    if isinstance(c, list):
        parts = []
        for block in c:
            if not isinstance(block, dict):
                continue
            if block.get('type') == 'text':
                parts.append(block.get('text', ''))
            elif block.get('type') == 'tool_use':
                parts.append(f'[{block.get("name", "tool")}]')
            elif block.get('type') == 'tool_result':
                parts.append(f'[result]')
        return ' '.join(parts).strip()
    return str(c)


@VisiData.api
def open_claude(vd, p):
    if p.is_dir():
        return ClaudeProjectsSheet(p.base_stem, source=p/"projects")
    # single jsonl session file
    return ClaudeSessionSheet(p.base_stem, source=p)


# rowdef: AttrDict with name, path, nsessions
class ClaudeProjectsSheet(Sheet):
    'Browse Claude projects'
    rowtype = 'projects'
    columns = [
        Column('name', getter=lambda c, r: r.name, width=50),
        Column('sessions', type=int, getter=lambda c, r: r.nsessions),
    ]

    def iterload(self):
        for entry in sorted(self.source.iterdir()):
            if not entry.is_dir():
                continue
            nsessions = sum(1 for f in entry.iterdir() if f.name.endswith('.jsonl'))
            yield AttrDict(name=entry.name, path=entry, nsessions=nsessions)

    def openRow(self, row):
        return ClaudeSessionsSheet(row.name, source=Path(str(row.path)))


def _session_meta(p):
    'Read first few lines of a session jsonl to get metadata.'
    meta = AttrDict(path=p, sessionId=p.stem, timestamp=None, first_msg='', nmsgs=0)
    try:
        with open(str(p)) as f:
            for line in f:
                obj = json.loads(line)
                t = obj.get('type')
                if t in ('user', 'assistant'):
                    meta.nmsgs += 1
                    if not meta.timestamp:
                        meta.timestamp = obj.get('timestamp')
                    if t == 'user' and not meta.first_msg:
                        msg = obj.get('message', {})
                        text = _content_text(msg)
                        # skip system/command messages
                        if text and '<command-name>' not in text and '<local-command' not in text:
                            meta.first_msg = text[:200]
    except Exception:
        pass
    return meta


# rowdef: AttrDict from _session_meta
class ClaudeSessionsSheet(Sheet):
    'Browse sessions in a Claude project'
    rowtype = 'sessions'
    columns = [
        Column('session', width=0, getter=lambda c, r: r.sessionId),
        Column('date', type=date, getter=lambda c, r: _ts(r.timestamp)),
        Column('messages', type=int, getter=lambda c, r: r.nmsgs),
        Column('first_message', width=80, getter=lambda c, r: r.first_msg),
    ]

    def iterload(self):
        for entry in sorted(self.source.iterdir()):
            if entry.name.endswith('.jsonl'):
                yield _session_meta(entry)

    def openRow(self, row):
        return ClaudeSessionSheet(row.sessionId, source=Path(str(row.path)))


# rowdef: AttrDict with type, role, timestamp, content, raw
class ClaudeSessionSheet(Sheet):
    'Browse messages in a Claude session'
    rowtype = 'messages'
    columns = [
        Column('type', getter=lambda c, r: r.type, width=10),
        Column('role', getter=lambda c, r: r.role, width=0),
        Column('timestamp', type=date, width=0, getter=lambda c, r: _ts(r.timestamp)),
        Column('content', getter=lambda c, r: r.content)
    ]

    def iterload(self):
        with open(str(self.source)) as f:
            for line in f:
                obj = json.loads(line)
                t = obj.get('type', '')
                msg = obj.get('message', {})
                role = msg.get('role', '') if isinstance(msg, dict) else ''
                content = _content_text(msg) if isinstance(msg, dict) else ''
                yield AttrDict(
                    type=t,
                    role=role,
                    timestamp=obj.get('timestamp'),
                    content=content,
                    raw=obj,
                )


vd.addGlobals(
    ClaudeProjectsSheet=ClaudeProjectsSheet,
    ClaudeSessionsSheet=ClaudeSessionsSheet,
    ClaudeSessionSheet=ClaudeSessionSheet,
)
