#!/usr/bin/env python3

import sys
import json

import difflib

def stderr(*args):
    print(*args, file=sys.stderr)

def progress(s):
    print(f"\r{s}", end='', file=sys.stderr)
    sys.stderr.flush()

def find_words_around(needle:dict, haystack:list[dict], seconds=10):
    return [w
        for w in haystack
            if abs(needle['start']-w['start']) < seconds]

def _score(whisperw, humanw):
    r = 0
    if whisperw.get('speaker') == humanw.get('speaker'):
        r += 5

    w1 = clean(whisperw.get('word', whisperw.get('text')))
    w2 = clean(humanw['text'])
    r += difflib.SequenceMatcher(a=w1, b=w2).ratio()*10

    r -= abs(whisperw['start'] - humanw['start'])
    return r

def clean(s:str) -> str:
    return ''.join(c.lower() for c in s if c.isalnum())

def main(humanfn, *whisperfns):
    mdt = json.loads(open(humanfn).read())

    poss = []
    for whisperfn in whisperfns:
        whispert = json.loads(open(whisperfn).read())
        word_timings = whispert['word_segments']

        for row in mdt['word_segments']:
            startt = row.get('start') or 0
            progress(f"{startt:.01f}")
            if row['speaker'] == 'marker':
                continue
            for humanw in row['subrows']:
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
#        humanw['text'] += f" {i}"
        whisperw['used'] = humanw

    for row in mdt['word_segments']:
        if row.get('speaker') == 'marker':
            continue
        if not row.get('subrows'):
            stderr('no subrows', row)
            continue
        row['start'] = row['subrows'][0]['start']
        row['end'] = row['subrows'][-1]['end']

    mdt['sourceaudio'] = 'daw/2025-10-16.mp3'
    print(json.dumps(mdt))


main(*sys.argv[1:])
