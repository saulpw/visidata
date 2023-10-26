'''
# Using VisiData with Google Sheets and Google Drive

## Setup and Authentication

Add to .visidatarc:

    import visidata.experimental.google

When VisiData attempts to use the Google API, it uses the "web authentication flow", which causes a web page to open asking for permissions to read and/or write your Google Sheets.
After granting permissions, VisiData caches the auth token in the .visidata directory.  Remove `.visidata/google-*.pickle` to unauthenticate.

## Load a Google Sheet into VisiData

Use VisiData to open the URL or spreadsheet id, with filetype `g` (or `gsheets`):

    vd https://docs.google.com/spreadsheets/d/1WV0JI_SsGfmoocXWJILK2nhfcxU1H7roqL1HE7zBdsY/ -f g

VisiData assumes the first row is the header row with column names.

## Save one or more sheets in VisiData as a Google Sheet

Save to `<sheetname>.g` using either `Ctrl+S` (current sheet only) or `g Ctrl+S` (all sheets on the sheet stack).
<sheetname> will be the visible name of the Spreadsheet in Google Drive; each sheet tab within the Spreadsheet will be named according to the sheet name within VisiData.

## List files in Google Drive

Use the `gdrive` filetype (the path doesn't matter):

    vd . -f gdrive

- Files can be marked for deletion with `d` and execute those deletions with `z Ctrl+S` (same as on the DirSheet for the local filesystem).
- Images can be viewed with `Enter` (in browser).
'''

import visidata.experimental.gdrive
import visidata.experimental.gsheets
