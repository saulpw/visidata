# VirtualRC Bot Load

Import the library and set the API key options in .visidatarc:

    import vdplus.virtualrcbot   # note: not included in vdplus by default

    options.vrc_app_id = ''
    options.vrc_app_secret = ''

## Usage

    vd anything.vrc

It starts out with a textual view of the space.  (not scrollable yet; to see more, expand the terminal window).

### Commands

- `Backtick` to view the "backing source" (entities in the space as rows of data)
- `b` to add a bot, `gb` to add multiple bots
- `1` to push the sheet of API responses
- `2` to push the sheet of subscription updates

and other commands from TextCanvas as useful in DarkDraw and others (`s`/`t`/`u` and variants to select/toggle/unselect objects under cursor, `HJKL` to slide selected, etc)

On the backing source sheet, edit values or delete rows and then `z Ctrl+S` to commit changes via the API.
