
# Authenticating

When VisiData attempts to use the Google API, it uses the "web authentication flow", which causes a web page to open asking for permissions to read and/or write your Google Sheets.
After granting permissions, VisiData caches the auth token in the .visidata directory.  Remove .visidata/google-\* to unauthenticate.

# Loading a Google Sheet into VisiData

Use VisiData to open the URL or spreadsheet id, with filetype `gsheets`:

    vd https://docs.google.com/spreadsheets/d/1WV0JI_SsGfmoocXWJILK2nhfcxU1H7roqL1HE7zBdsY/ -f gsheets

VisiData assumes the first row is the header row with column names.

# Saving one or more sheets in VisiData as a Google Sheet

Save to `<sheetname>.gsheet` using either `Ctrl+S` (current sheet only) or `g Ctrl+S` (all sheets on the sheet stack).
"sheetname" will be the visible name of the Spreadsheet in Google Drive; each sheet tab within the Spreadsheet will be named according to the sheet name within VisiData.
