# Using Airtable with VisiData

## Setup

Obtain your [personal API key](https://airtable.com/account) and add it to `.visidatarc`:

    import vdplus.api.airtable
    options.airtable_key = 'keyXXXXXXXXXXXXXX'

## Loading an Airtable table into VisiData

To load a table, first obtain its base ID by visiting the [API documentation](https://airtable.com/api) and selecting the base containing the table.
The base ID is a string beginning with "app".
It can be passed on the command-line or added to `.visidatarc`:

    options.airtable_base = 'appXXXXXXXXXXXXXX'

Use VisiData to open the URL of an Airtable table, with filetype `airtable`:

    vd -f airtable --airtable_base=appXXXXXXXXXXXXXX https://airtable.com/tblXXXXXXXXXXXXXX/viwXXXXXXXXXXXXXX

## Saving changes to an Airtable table

Changes made to an Airtable table in VisiData can be committed back to Airtable using `z Ctrl+S`.
