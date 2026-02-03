- when rollup with g), don't put it at the cursor, put it at the 
   - put cursor on rolled up line
- rollup all sections?
- preserve cut amount with 'a'
- only colorize text for 'cut' sections?
- use background instead of underline for section start
- use underline for playhead?
- 'a' after last word creates two empty rows?
- cut text should not be shown in rolled up text in vd?

- flag words or lines as incorrect for cleanup review

- single-word interjections inlined into other paragraph
- combine consecutive cuts in markdown
- bug: batch convert transcript to xmd "terminated"

- feat: play side subsheet of rows (if in order)
- feat: edit text of subwords while maintaining timings
- output should descend into EditRow; lower headers are subheaders?

- feat: replace line with separate stem (e.g. AI generated voice)

- ) to reclose current row.  or is that too much given ENTER/q?


- command to rollup whisper transcript by speaker again
   - like the .xmd output grouping

? sequential cut lines should show up as single …
? select to next marker
? command to select rows from last marker (zs)

- cleanup: rename PodcastEditingSheet to Transcript[Editing]Sheet

? highlight current word in transcript

- track cutpoints as times
- feat: z< and z> to adjust the previous cutpoint
   - play 100ms tone at marker

- feat: 1-9 for numbered (temporary) marker
   - 'z1' to set marker 1 at current timestamp; '1' to play starting at marker 1

7. outputs
   + c) transcript with cuts excluded (transcript of edited audio) -- based on options.daw_include_cuts
   d) edited audio (pasting non-cut sections together)
   e) .omf file for use in other DAW like reaper
