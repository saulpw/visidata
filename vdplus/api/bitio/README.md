# Using VisiData with bit.io

## Setup

[Get your bit.io API key](https://docs.bit.io/docs/connecting-via-the-api) and add this to .visidatarc:

    import vdplus.api.bitio
    options.bitio_api_key='...'

## Usage

To list repos for a given user:

    vd -f bitio <username>

Repo fields are editable (deferred; save with `z Ctrl+S` as always).
Press `Enter` to view the tables in a repo; press `Enter` to load a table.
