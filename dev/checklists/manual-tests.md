# Functionality to test manual
1. cmdlog + replay
    - logging of options
    - logging of rows and columns
    - if empty sheet, row or column on cmdlog, executes command on current sheet, row, column
    - abort
    - test batch mode
        - bin/vd -b -p tests/append.vd
        - bin/vd -p tests/append.vd -b
4. longname-exec
5. syscopy
6. plots and image-loaders (like png)
    - relationship between plots and mice
10. large dataset (311)
15. Test loading url
    - http url load + open-row html-link (#22) automated against a loopback server in tests/test-url.sh
    - manual residual: a real external https url (e.g. https://visidata.org/usage.tsv) — TLS + live network, not in CI
16. Split window
    - make sure that if you exit split window, all the sheets from both panes can be accessible on the resulting stack
    - test 1
        - open 2 files
        - Z
        - first window should be active
        - Tab between
        - close top one, then redo and test closing bottom one
    - test 2
        - open 2 files
        - Z
        - open columns sheet in one
        - Z
        - inspect sheet stack
            - columns sheet should remain where it is, and the source sheet below gets moved to the top of the other window
        - redo with opening the columns sheet on the other
            - bug
                - when Shift+Z is done on bottom pane, its second sheet becomes the second sheet of the top stack, instead of the first sheet of the top stack
        - test 3
            - Shift+Z with only one file
            - Shift+Z with two panes, each pane's stack only has one file
    - gZ
        - test both panes
        - move around, should be no flickering
        - press Z again
        - test both panes
    - zZ
        - should change window size, without changing anything else
        - test for both panes
        - test negative and positive
            - bug?
                - negative switches the windows they belong to
    - gTab
        - should window swap
        - test both panes
            - bug?
                - if the second window is a smaller size, should it orient around the cursor position
    - using cursor in active pane
        - test both panes
17. Anything new in this release (should it have its own automated test?)
18. `edit-cell` and then `Ctrl+O` while editing actually opens $EDITOR and the cell takes the editor result.
    - the launch+readback mechanism is automated in visidata/tests/test_editor.py; only the in-editor Ctrl+O keystroke is manual
19. Save with overwrite=c onto an existing file: at the `<file> exists. overwrite?` prompt, confirm y/n actually overwrites/aborts.
    - the rest of save/overwrite (fallback, block, overwrite=y/n, multi-sheet) is automated in tests/test-save.sh + tests/test-filetype.sh
21. Test macro-record.
22. Test `open-row` on a real external html link (e.g. https://hls.gsfc.nasa.gov/data/ or a Wikipedia page).
    - the open-row link-following mechanism is automated in tests/test-url.sh; this residual is real-world HTML over live https
24. Test adding multiple aggregators via palette (+)
25. time vd -p tests/quit-nosave.vdj  - note down the time. compare to PR #2369
26. Use the z; command. Then type in a command line like echo "| Ceci n'est pas une pipe"
27. vd -b -i -p tests/fill.vdj sample_data/a.tsv
Check that both benchmark and a.tsv are edittable.

## Cursor/Scrolling
28. scroll all the way down with j
29. pgdn from 1, stay at top, exactly one page forward
30. 3xj, pgdn from there, relative cursor position stays
31. ZZ
