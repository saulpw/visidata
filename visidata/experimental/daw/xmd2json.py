#!/usr/bin/env python3

'''
Usage: $0 <human_transcript.md> <whisper_transcript.json...>

Parse the human_transcript.md, and match the words from whisper_transcript.json to provide the word-level timings.  Output centaur_transcript.json.
'''

import sys
import copy
import re
import json

TODO = '''

## ideas to better align

- bug: Intro header on wrong line
- rename 'word' column to 'text'
'''

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
    headers = []
    for line in open(xmdfn):
        line = line.strip()
        if not line: continue
        if line.startswith('#'):
            n = len(line) - len(line.lstrip('#')) - 1
            headers = headers[:n+1] + ['']*(n - len(headers)+1)
            headers[n] = line[n+1:]
        else:
            m = re.match(r'(?P<start_cut>~~)?\\?(\[(?P<start>[\d:\.]+)\\?\] )?((?P<speaker>[A-Za-z]+): )?(?P<word>.*)', line)
            if not m:
                print('Unmatched: ' + line)
                return rows

            row = m.groupdict()

            row['speaker'] = row.get('speaker')
            if not row['speaker']:
                if pending_rows:
                    row['speaker'] = pending_rows[-1].get('speaker')
                elif rows:
                    row['speaker'] = rows[-1].get('speaker')

            lastt = row['start'] = parse_hhmmss(row.get('start'))

            if lastt:
                if pending_rows:
                    firstt = float(pending_rows[0]['start'])
                else:
                    firstt = 0

                if headers:
                    row['marker'] = headers[-1]
                    headers = []

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

            for newrow in split_cuts(row, row.pop('start_cut', False)):
                pending_rows.append(newrow)

    return rows


def main(xmdfn):
    print(json.dumps(dict(word_segments=parse_xmd(xmdfn))))


main(*sys.argv[1:])
