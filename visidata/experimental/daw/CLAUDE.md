# VisiData Audio Workstation (vdaw)

## Overview

This is an experimental VisiData plugin for editing podcast transcripts with synchronized audio playback. It provides a terminal-based interface for reviewing word-level transcripts, marking cuts, editing speaker labels, and exporting edited transcripts.

## Architecture

### Core Components

**vdaw.py** - Main sheet implementation and editing logic
- `EditRow` class: Hierarchical row structure representing transcript segments
  - Supports nested subrows (sections → lines → words)
  - Tracks cut/keep state, speaker, timestamps (start/end), and text
  - Implements splitting operations (split_at_word, split_at_time)
  - Uses `@drawcache_property` for expensive computations (text, duration, uncutrows)
- `PodcastEditingSheet`: VisiData Sheet subclass for transcript editing
  - Manages row hierarchy and playback cursor synchronization
  - Integrates with MpvProcess for audio playback
  - Handles cut detection during playback (skipcut mode)
  - Binary search for finding rows by timestamp (find_row_path)
- Export formats: `.transcript` (JSON), `.xmd` (markdown with timestamps), `.cutlist`

**mpv.py** - Audio playback via mpv IPC
- `MpvProcess`: Manages mpv subprocess and Unix socket communication
- Audio filter support (agate, loudnorm) with parameter adjustment
- Real-time filter parameter modification triggers mpv restart
- Socket-based commands: play, pause, seek, property queries

**merge_transcripts.py** - Merges human-edited transcript with whisperx word timings
- Matches words between human transcript and whisperx output using fuzzy matching
- Scores based on speaker match, text similarity (difflib), and time proximity
- Outputs combined transcript with accurate word-level timestamps

**xmd2json.py** - Parses markdown transcripts into JSON format
- Format: `[HH:MM:SS.s] **Speaker**: text` with optional section headers (`##`)
- Handles strikethrough for cuts (`~~text~~`)
- Interpolates timestamps for lines without explicit timing
- Splits lines into word-level subrows

### Data Flow

```
Audio file
  → AI-generated transcript with word-level timings
  → VisiData (vd -f transcript)
  → editing in PodcastEditingSheet
  → export as .xmd (markdown) or .transcript (JSON)
```

### Key Design Patterns

1. **Hierarchical Rows**: EditRow supports arbitrary nesting. Top-level rows are sections/paragraphs, mid-level are lines, bottom-level are individual words with timestamps.

2. **Cut State Propagation**: If a row has subrows, its cut state is max of subrow cuts. Otherwise, it's explicitly set. Negative cut values indicate cuts to remove.

3. **Playhead Synchronization**: `checkCursor()` is called during playback to:
   - Skip over cut segments when skipcut=True
   - Find the current word via binary search (find_row_path)
   - Seek to next uncut word if in a cut segment

4. **Draw Cache**: Expensive properties (text, duration, uncutrows) use `@drawcache_property` which clears on every fresh draw cycle.

## Common Commands

### Running vdaw

Load a transcript (requires matching .wav or .mp3 file for synced playback):
```bash
vd editable-transcript.json -f transcript
# or with .transcript extension:
vd editable-transcript.transcript
```

### Key Editing Commands

See README.md for the complete list of editing commands.

### Exporting

- Save as `.xmd` for markdown transcript with strikethrough cuts
- Save as `.cutlist` for a human-readable list of cut segments
- Save as `.transcript` or `.json` for the full editable format

## Development Notes

### Adding New Features

- All VisiData commands are added via `Sheet.addCommand()` at bottom of vdaw.py
- New columns should be added to `PodcastEditingSheet.columns` list
- Use `vd.addUndo()` before modifying sheet.rows to enable undo
- Call `sheet.setModified()` when making edits to trigger save prompts

### Timestamp Handling

- All timestamps are floats (seconds since start)
- `to_hms()` formats timestamps as `HH:MM:SS.s` or `MM:SS.s` format
- Words without valid timestamps have `start=None, end=None`
- `flag_bad_timings()` identifies and interpolates invalid timings

### mpv Integration

- mpv runs in separate process, controlled via Unix socket at `/tmp/vdmpv`
- Filter changes require mpv restart (see `restart_mpv()`)
- Playback queries (`playback_time`, `paused`) are synchronous socket calls
- Clean up leftover mpv processes: `pkill -f vdmpv` or restart with `Ctrl+R`
