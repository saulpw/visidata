# [RC Together](https://www.rctogether.com/) Interface and Bot Controller

Useful for exploring the underlying data, and creating and modifying bots in bulk.

## Setup

Import the library and set the API key options in .visidatarc:

    import vdplus.api.rctogether
    options.rc_app_id = ''
    options.rc_app_secret = ''

## Usage

    vd recurse.rc

where `recurse` is the realm to use (which will use `recurse.rctogether.com` as the API and websocket endpoint).

It starts out with a textual view of the space.  (not scrollable yet; to see more, expand the terminal window).

### Commands

- `Backtick` to toggle between the "backing source" (entities in the space as rows of data) and the world.
- `b` to add a bot at the cursor; `gb` to add multiple bots

(Use `Space` to execute commands by longname)

- `open-rc-msgs` to push the sheet of API responses
- `open-rc-stream` to push the sheet of subscription updates

and other commands from TextCanvas as useful in [DarkDraw](https://github.com/devottys/darkdraw) and others (`s`/`t`/`u` and variants to select/toggle/unselect objects under cursor, `HJKL` to slide selected, etc)

On the backing source sheet, edit values or delete rows, then `z Ctrl+S` to commit changes via the API.
