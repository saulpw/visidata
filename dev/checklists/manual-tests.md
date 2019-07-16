# Functionality to test manual
1. cmdlog + replay
    - logging of options
    - logging of rows and columns
    - pause, continue, abort
2. piping data into visidata
4. longname-exec
5. syscopy
6. plots and image-loaders (like png)
    - relationship between plots and mice
7. savers and gSavers
8. .visidatarc
    - numerical, boolean and string option
    - sheet-specific and global
    - motd_url
9. using the pandas loader
10. large dataset (311)
11. multiline scrolling tests
    - test case 1
        - use vgit
        - main status sheet is 1 line per row, scroll down manually to the bottom
        - and past, ensure it scrolls well
        - and then scroll to the top, and make sure it scrolls back
     - test case 2
        - start a few down from the top
        - Ctrl+F
        - make sure the cursor stays relatively positioned
        - Ctrl+F and Ctrl+B should be reserves, at least in the middle of the sheet
        - and then all the way to the bottom; j does nothing
        - gj always puts the cursor on the bottom row
     - test case 3
        - Shift+L for log, same tests
