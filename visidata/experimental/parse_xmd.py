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

- compute estimated individual word starts (spread them evenly)

- integrate each mic transcription separately

- for each whisper word,
  - find words in the transcript around the whisper time (within a few seconds)
  - calc a score based on
    - speaker match (+5)
    - word match (+n letters matching)
    - time alignment (+1 if within a second)

- rename 'word' column to 'text'
'''

def clean(s:str) -> str:
    return ''.join(c.lower() for c in s if c.isalnum())

def parse_hhmmss(hms:str) -> float:
    if not hms:
        return hms
    h, m, s = hms.split(':')
    return int(h)*3600 + int(m)*60 + float(s)


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
            d['speaker'] = d.get('speaker') or rows[-1].get('speaker')

            lastt = d['start'] = parse_hhmmss(d.get('start'))

            if lastt:
                firstt = float(pending_rows[0]['start'])
                total_len = sum(len(r['word']) for r in pending_rows)
                for i, nytr in enumerate(pending_rows):
                    if i > 0:
                        nytr['start'] = pending_rows[i-1]['end']
                    nytr['end'] = (len(nytr['word'])/total_len)*(lastt-firstt)+nytr['start']

                    if nytr.get('start_cut'):
                        del nytr['start_cut']
                        nytr['word'] = '~~' + nytr['word']

                    parts = nytr['word'].split('~~')
                    cut = False
                    for p in parts:
                        newrow = copy.copy(nytr)
                        newrow['word'] = p.strip()
                        if cut:
                            newrow['cut'] = True
                        if p:
                            rows.append(newrow)
                        cut = not cut

                pending_rows = []
            pending_rows.append(d)

    return rows


def combine_transcripts(mdt, whispert):
    '''mdt has accurate speakers and words; whispert has accurate word-level timestamps'''

    word_timings = whispert['word_segments']

    for row in mdt['word_segments']:
        if row['speaker'] == 'marker':
            continue
        row['baserows'] = []
        for w in row['word'].split():
            found = False
            #print(w)
            for i, wordt in enumerate(word_timings):
                if i > 3:
                    break  # didn't find it :(

                #print(wordt)
                # - compare only words, no punctuation
                if clean(wordt['word']) == clean(w):
                    found = True
                    #print('found it')
                    d = dict(start=wordt['start'],
                             end=wordt['end'],
                             speaker=row['speaker'],
                             word=w)
                    row['baserows'].append(d)
                    break

            if found:
                del word_timings[:i+1]  # remove everything to this point
    return mdt


def main(xmdfn, *whisperfns):
    mdt = dict(word_segments=parse_xmd(xmdfn))

    for whisperfn in whisperfns:
        whispert = json.loads(open(whisperfn).read())
        mdt = combine_transcripts(mdt, whispert)

    mdt['sourceaudio'] = 'daw/2025-10-16.mp3'
    print(json.dumps(mdt))


main(*sys.argv[1:])
