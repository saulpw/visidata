#!/usr/bin/env python3

'''
Usage: $0 <human_transcript.md> <whisper_transcript.json...>

Parse the human_transcript.md, and match the words from whisper_transcript.json to provide the word-level timings.  Output centaur_transcript.json.
'''

import sys
import copy
import re
import json
import difflib

TODO = '''



## ideas to better align

- set 'cut' for each word in baserows
- rename 'word' column to 'text'
'''

def clean(s:str) -> str:
    return ''.join(c.lower() for c in s if c.isalnum())

def parse_hhmmss(hms:str) -> float:
    if not hms:
        return hms
    h, m, s = hms.split(':')
    return int(h)*3600 + int(m)*60 + float(s)


def interpolate_times(pending_rows:list[dict], startt, endt):
    total_len = sum(len(r['word']) for r in pending_rows)
    for i, pr in enumerate(pending_rows):
        if i > 0:
            pr['start'] = pending_rows[i-1]['end']
        else:
            pr['start'] = startt
        pr['end'] = (len(pr['word'])/total_len)*(endt-startt)+pr['start']

    return pending_rows


def split_cuts(row, startcut=False):
    parts = row['word'].split('~~')
    cut = startcut  # whether we start in cut mode
    for p in parts:
        p = p.strip()
        if p:
            newrow = copy.copy(row)
            newrow['word'] = p
            if cut:
                newrow['cut'] = cut
            yield newrow

        cut = not cut

def parse_xmd(xmdfn:str) -> list:
    rows = []
    pending_rows = []
    for line in open(xmdfn):
        line = line.strip()
        if not line: continue
        elif line.startswith('#'):
            t = rows[-1]['end'] if rows else 0
            d = dict(speaker='marker', start=t, end=t, word=line)
            rows.append(d)
        else:
            m = re.match(r'(?P<start_cut>~~)?\\?(\[(?P<start>[\d:]+)\\?\] )?((?P<speaker>[A-Za-z]+): )?(?P<word>.*)', line)
            if not m:
                print('Unmatched: ' + line)
                return rows

            d = m.groupdict()
            if d['speaker'] == 'marker':
                rows.append(d)
                continue

            d['speaker'] = d.get('speaker') or (pending_rows[-1].get('speaker') if pending_rows else rows[-1].get('speaker'))

            lastt = d['start'] = parse_hhmmss(d.get('start'))

            if lastt:
                firstt = float(pending_rows[0]['start'])
                for pr in interpolate_times(pending_rows, firstt, lastt):
                    pr['baserows'] = interpolate_times([
                        dict(start=None, end=None,
                             speaker=pr['speaker'],
                             cut=pr.get('cut'),
                             word=w)
                          for w in pr['word'].split()
                      ], pr['start'], pr['end'])
                    rows.append(pr)

                pending_rows = []

            for newrow in split_cuts(d, d.pop('start_cut', False)):
                pending_rows.append(newrow)

    return rows

def find_words_around(needle:dict, haystack:list[dict], seconds=10):
    return [w
        for w in haystack
            if abs(needle['start']-w['start']) < seconds]

def stderr(*args):
    print(*args, file=sys.stderr)

def progress(s):
    print(f"\r{s}", end='', file=sys.stderr)
    sys.stderr.flush()


def _score(whisperw, humanw):
    r = 0
    if whisperw.get('speaker') == humanw.get('speaker'):
        r += 5

    w1 = clean(whisperw['word'])
    w2 = clean(humanw['word'])
    r += difflib.SequenceMatcher(a=w1, b=w2).ratio()*10

    r -= abs(whisperw['start'] - humanw['start'])
    return r


def main(xmdfn, *whisperfns):
    mdt = dict(word_segments=parse_xmd(xmdfn))

    poss = []
    for whisperfn in whisperfns:
        whispert = json.loads(open(whisperfn).read())
        word_timings = whispert['word_segments']

        for row in mdt['word_segments']:
            progress(f"{row['start']:.01f}")
            if row['speaker'] == 'marker':
                continue
            for humanw in row['baserows']:
                for whisperw in find_words_around(humanw, word_timings):
                    poss.append((_score(whisperw, humanw), whisperw, humanw))

    poss.sort(key=lambda r: -r[0])

    i = 0
    for score, whisperw, humanw in poss:
        if whisperw.get('used'):
            continue

        if humanw.get('match_score'):
            continue

        i += 1
        humanw['start'] = whisperw['start']
        humanw['end'] = whisperw['end']
        humanw['match_score'] = score
#        humanw['word'] += f" {i}"
        whisperw['used'] = humanw

    for row in mdt['word_segments']:
        if row.get('speaker') == 'marker':
            continue
        if not row.get('baserows'):
            stderr('no baserows', row)
            continue
        row['start'] = row['baserows'][0]['start']
        row['end'] = row['baserows'][-1]['end']

    mdt['sourceaudio'] = 'daw/2025-10-16.mp3'
    print(json.dumps(mdt))


main(*sys.argv[1:])
