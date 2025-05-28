---
eleventyNavigation:
    key: Customizing VisiData - Colors
    order: 12
update: 2023-10-12
version: VisiData v3.0
---

## Color Options

Interface elements and colors can be set on the command-line before a session, or in .visidatarc to take effect for every session, or within VisiData on the Options Sheet (`Shift+O`).  Color options in particular start with `color_`:

    vd --color-selected-row="magenta"

or in .visidatarc:

    options.color_selected_row = "magenta"

On the Options Sheet, if you edit a color (or any display element), you will see the changes immediately, both in the options value (which is itself colorized) and also in the interface.  `Shift+U` to undo if you don't like it.

![vd color options sheet](/docs/assets/vd-screenshot-options-colors.png)

## Color Specification

Colors in the terminal have 3 components: *foreground*, *background*, and *attributes*.
In most modern terminals, each of the foreground and background colors can be one of 256 colors in a standard palette.

Several attributes are also available: `bold`, `italic`, `reverse`, and `underline`.  (There are other attributes like `dim` and `blink`, but they are not widely supported).

In VisiData, colors are specified with a simple language:

    <attribute> <fg-color> on <bg-color>

where `<attribute>` is a plain text name as above, and each `<color>` is a number from 0-255, or a basic color name from the original 8-color palette: `black red green yellow blue magenta cyan white`.
Multiple attributes may be specified.

Most terminals support 256 colors, but because some do not, it's possible to specify a *fallback color*, which is a second color that's used in case the first color isn't available.
For instance, `215 yellow` means to use the color `215` (kind of orange-brown), but if it's not available, use `yellow` instead.

Multiple colors may be applied to a single interface element with different precedence, for instance with [colorizers](docs/api/interface).
The color used will be the highest precedence background and the highest precedence foreground, which may come from separate color strings.  All attributes will be applied regardless of precedence--there is no way to specify a negative attribute or "no" attributes.

Any of the color components may be omitted, letting that component be given by a lower-precedence colorizer instead, ultimately falling back to `color_default` (`white on black` in the default theme).
Many color strings only specify a single attribute.

The ordering above--attributes first, then foreground, and finally background--is suggested and preferred.
Attributes may be specified anywhere in the color string; this does not change their effect (e.g. `bold` applies to the font rendered, not to the foreground or background color, even if `bold` text makes the foreground color seem brighter).
The `reverse` attribute flips the foreground and background color.  Multiple `reverse` attributes do not undo each other.

## 256 Terminal Colors and the Colors Sheet

To see all the available colors and what they look like in your specific terminal, run the `open-colors` command.  (This command is not bound to any keystroke, so must be executed by its longname; press `Space`, then type `open-colors`, then press `Enter`.)

![vd open-colors](/docs/assets/vd-screenshot-colors-sheet.png)

The first several rows on this sheet are the existing color strings that are currently in use.
After these are the numeric colors; note that colors 0-7 correspond to the named colors above, with 0 being black and 7 being standard white.  Colors 8-15 are unnamed brighter versions of these colors: 8 is gray ("bright black") and 15 is bright white.

Colors 16-231 form a regular color cube with a wide variety of gradations covering the color space.
Colors 232-255 are gradients of white, with 232 being the darkest possible gray (almost indistinguishable from the black of 0 and 16), and 255 being almost the brightest white (though 15 is brighter).

## [Changing Display Attributes within a string](#attrs) {#attrs}

In many interface elements, it's possible to change the display attributes inline, within a single string.
For example, the menu bar has a message displayed in the upper right (which by default shows "Ctrl+H for help menu"), and is configurable with `options.disp_menu_fmt`.
The base menu color is configurable with `options.color_menu`, which is also applied to this menubar message.
However, this can be changed by specifying a new color within the string itself, using syntax like `[:red]`:

    options.disp_menu_fmt = "[:red on black]{vd.motd}"

A color option name can also be used instead of a real color; for example, to use the `color_error` color, use `[:error]`:

    options.disp_menu_fmt = "[:error]{vd.motd}"

Attribute changes can happen multiple times in a single string.
Use `[/]` to clear the last inline color change, and `[:]` to clear all inline attributes:

    options.disp_menu_fmt = "[:underline]Note:[/] [:error]{vd.motd}"

What follows the `/` is not checked, so these are all valid:

    [:underline]underlined text[/underline]
    [:underline]also underlined[/]
    [:underline]underline ends at end of string

### onclick

In addition to changing the display attributes, an `onclick` attribute can be given with this inline syntax, which specifies either a VisiData command to run, or a url to open (in `$BROWSER`), when the interface element is clicked:

    options.disp_menu_fmt = "[:onclick https://jsvine.github.io/intro-to-visidata/]Click here to go to the tutorial[/]"

Or if you want a custom VisiData toolbar some of your favorite actions:

    vd --disp_menu_fmt="[:onclick freq-col] freq out [/] | [:onclick quit-sheet] back [/]"

Elements with `onclick` are displayed with `color_clickable`, which is by default `underline`, which is commonly understood as a clickable affordance.

## Setting the Theme

A set of configured display elements and attributes may be packaged into a *theme*, which can be set as an option before VisiData starts (on the CLI or in .visidatarc), and can be changed with the `theme-input` command (in the menu under `View > Set theme`).

By default VisiData uses a dark-mode color scheme and some suggestive Unicode characters.
A few non-default themes are also packaged with VisiData:

- [`light`](https://github.com/saulpw/visidata/blob/develop/visidata/themes/light.py): light-mode color scheme
- [`ascii8`](https://github.com/saulpw/visidata/blob/develop/visidata/themes/ascii8.py): ascii characters and basic 8-colors only
- [`asciimono`](https://github.com/saulpw/visidata/blob/develop/visidata/themes/asciimono.py): ascii characters and default colors only

To use VisiData on a classic [DEC VT102](https://terminals-wiki.org/wiki/index.php/DEC_VT102) terminal:

    vd --theme=asciimono

[I would [love to know](https://github.com/saulpw/visidata/discussions/1533) of anyone using VisiData in such a lo-fi situation!]

### Adding a new theme

To add another theme, add it to the `vd.themes` dictionary in .visidatarc.
If more than one person uses it, [submit a PR](https://github.com/saulpw/visidata/pulls) to include it in the [visidata/themes](https://github.com/saulpw/visidata/tree/develop/visidata/themes) directory.

    vd.themes['awesome'] = dict(
        color_default      = 'black on white',  # the default fg and bg colors
        color_key_col      = '20 blue',   # color of key columns
        color_edit_cell    = '234 black',     # cell color to use when editing cell
        # ... etc
    )

## Colorizers

`TableSheet` sheets (which is any sheet with a row/column grid, i.e. most sheets) have *colorizers*, functions that can provide display attributes on individual rows, columns, or cells.

See [docs/api/interface](/docs/api/interface#colors) for how to use colorizers.
