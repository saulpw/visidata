# VisiData Pro

## Features

- [Google Drive](google/#gdrive)
  - list files
  - delete file
  - open image in browser
  - open Google Sheet in VisiData
- [Google Sheets](google/#gsheets)
  - load from url with `-f gsheets` (or `-f g`)
  - save with `.g` extension
- [Airtable](airtable.md)
  - load from url with `-f airtable`
  - save changes to existing tables with `z Ctrl+S`

## License

This repository is private, and only [Saul Pwanson](https://github.com/saulpw) has the authority to grant access to it or to distribute its contents.

The code in this repository, hereafter "VisiData Plus", is **not** open-source software.

Access to this repo grants you the ability to use the software according to the [LICENSE](LICENSE.md).

You **may** modify this source code for your own usage, and you **may** distribute those modifications as patches to other users of VisiData Plus, but you **must not** redistribute any of the source code contained in this repository.

## Installation

1. Clone this repo into `.visidata/vdplus`.

    git clone git@github.com:saulpw/vdplus ~/.visidata/vdplus

2. Add this line to your `.visidatarc` (which is usually in the $HOME directory):

    import vdplus

3. Install Python requirements:

    pip3 install -r ~/.visidata/vdplus/requirements.txt

4. Update to the [latest develop version of VisiData](https://github.com/saulpw/visidata/tree/develop).
