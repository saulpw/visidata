# VisiData Pro

## Features

- [Google Drive](#google)
  - list files
  - delete file
  - open image in browser
  - open Google Sheet in VisiData

- [Google Sheets](#google)
  - load from url with `-f gsheets` (or `-f g`)
  - save with `.g` extension
- [Airtable](airtable.md)
  - load from url with `-f airtable`
  - save changes to existing tables with `z Ctrl+S`
- [Reddit](reddit.md)
  - read-only interface to API for subreddits, redditors, submissions, and comments
- [Web Scraper](#scraper)
  - `vd <url> -f scrape` opens url in RequestsSheet
    - scraping results cached in sqlite db in .visidata
    - `ENTER` (open-row) to open row as HTMLElements

  - HTMLElements is list of elements as parsed by beautifulsoup4
    - easily determine selector containing relevant information
    - dive into children of cursor element with `ENTER` (or children of all selected rows with `g ENTER`)
    - batch open links to scrape more data with `go` to open RequestsSheet with hrefs in selected rows

  - on RequestsSheet, add column of elements matching given css selector with `;` (addcol-selector)
    - cross-tabulate data from multiple pages
    - join elements together with the `soupstr` type (bound to `~` on the HTMLElementsSheet)

## License

This repository is private, and only [Saul Pwanson](https://github.com/saulpw) has the authority to grant access to it or to distribute its contents.

The code in this repository, hereafter "VisiData Plus", is **not** open-source software.

Access to this repo grants you the ability to use the software according to the [LICENSE](LICENSE.md).

You **may** modify this source code for your own usage, and you **may** distribute those modifications as patches to other users of VisiData Plus, but you **must not** redistribute any of the source code contained in this repository.

## Installation

1. Clone this repo into `.visidata/vdplus`:

```
    git clone git@github.com:saulpw/vdplus ~/.visidata/vdplus
```

2. Add this line to your `.visidatarc` (which is usually in your home directory):

```
    import vdplus
```

3. Install Python requirements:

```
    pip3 install -r ~/.visidata/vdplus/requirements.txt
```

4. Update to the [latest develop version of VisiData](https://github.com/saulpw/visidata/tree/develop).


# Using Google Sheets and Google Drive

## Authenticating

When VisiData attempts to use the Google API, it uses the "web authentication flow", which causes a web page to open asking for permissions to read and/or write your Google Sheets.
After granting permissions, VisiData caches the auth token in the .visidata directory.  Remove `.visidata/google-*.pickle` to unauthenticate.

## Loading a Google Sheet into VisiData

Use VisiData to open the URL or spreadsheet id, with filetype `g` (or `gsheets`):

```
    vd https://docs.google.com/spreadsheets/d/1WV0JI_SsGfmoocXWJILK2nhfcxU1H7roqL1HE7zBdsY/ -f g
```

VisiData assumes the first row is the header row with column names.

## Saving one or more sheets in VisiData as a Google Sheet

Save to `<sheetname>.g` using either `Ctrl+S` (current sheet only) or `g Ctrl+S` (all sheets on the sheet stack).
<sheetname> will be the visible name of the Spreadsheet in Google Drive; each sheet tab within the Spreadsheet will be named according to the sheet name within VisiData.

## Google Drive

Use the `gdrive` filetype (the path doesn't matter):

```
    vd . -f gdrive
```

- Files can be marked for deletion with `d` and execute those deletions with `z Ctrl+S` (same as on the DirSheet for the local filesystem).
- Images can be viewed with `Enter` (in browser).
