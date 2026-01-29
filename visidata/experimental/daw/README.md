
# VisiData Audio Workstation

* current goal: automate getting functional transcript (80%+)
  so that i can actually make progress editing with vdaw
  which will close the loop and take vdaw to become a functional transcript audio editor

## getting the input transcript

Given a separate .wav file per speaker.

For each input .wav file:

1. Cut out the low volume audio, so the non-speaker doesn't get transcribed.

    ffmpeg -i mike.wav -af "agate=" mike-only.wav

2.  Use whisperx to get word-level timestamps.

    uvx whisperx --model base.en --task transcribe --hf_token ${HF_API_TOKEN} --highlight_words True --compute_type int8 --device cpu mike-only.wav

3.  (Optional) get full transcript from other source as .md to serve as the best/canonical edit.

    xmd2json.py transcript.md > transcript.json

4.  Then merge the per-speaker transcripts.

    merge_transcripts.py transcript.json mike-only.json saul-only.json > editable-transcript.json

5.  Load into VisiData using the `transcript` file format.

    vd editable-transcript.json -f transcript

## Saving changes

Modifications can be saved via `Ctrl+S` to the original .json file, or use a `.transcript` suffix for a bit more convenience (doesn't require the `-f` flag above).

### Export markdown

[Ideally VisiData should make it possible for a sheet to override a saver, so vdaw could define a save_md.]

For now, save as `foo.xmd` to get a markdown transcript with strikethrough for deleted lines.

## Editing Commands

### Playback
- `p` - Play from cursor row (skipping cuts)
- `P` - Play from cursor row (including cuts)
- `zp` - Toggle pause
- `[` / `]` - Seek backward/forward 10 seconds
- `g[` / `g]` - Seek backward/forward 60 seconds
- `gg` - Jump cursor to playhead
- `F5` - Slow down playback speed by 50%
- `F8` - Speed up playback 2x
- `Ctrl+R` - Restart mpv process

### Cutting/Keeping Audio
- `x` - Cut audio for line at cursor row
- `y` - Keep/upvote audio for line at cursor row
- `gx` - Cut audio for selected rows
- `gy` - Keep audio for selected rows

### Splitting & Combining
- `a` - Split line at current playhead
- `za` - Split line at word (prompts for word)
- `g)` - Combine selected rows into one
- `(` - Expand row into subrows
- `g(` - Expand selected rows

### Navigation
- `<` / `>` - Move to previous/next section header
- `g<` / `g>` - Move to first/last section header

### Text Formatting
- `r` - Reformat row (wrap text to column width)
- `gr` - Reformat selected rows

### Audio Filters
- `f` - Open audio filter parameters sheet
- `0-9` - Set filter parameter to preset value (in filter sheet or main sheet)

### Utilities
- `c` - Clean/interpolate bad word timings

## Applying ffmpeg filters

- Use vdaw to experiment with ffmpeg filters via the `f` command

     - agate
     - compand
     - loudnorm
