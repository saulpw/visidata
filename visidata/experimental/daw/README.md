
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

## applying ffmpeg fiters

- Use vdaw to experiment with ffmpeg filters

     - agate
     - compand
     - loudnorm
