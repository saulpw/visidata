---
eleventyNavigation:
    key: Command Menus
    order: 12
Updated: 2021-09-02
Version: VisiData v2.6
---

At the top of the screen, there's a typical application toplevel menubar:

    Sheet  Edit  View  Column  ...

You can press `Ctrl+H` to activate the Help menu (shown in the upper right).
Then you can use the arrow keys (or `hjkl` of course) to navigate the various commands and submenus.

`Enter` or `Space` will execute the command or dive into the submenu.

`q` or `Esc` or `Ctrl+Q` will leave the menu without taking an action.

## Other ways of opening the menu

`Alt+S` or `Alt+E` etc will open that specific submenu (see the underlined letter).
On Macos, `Option+S` etc should work the same (with the exception of `Option+E`, which needs to be `Option+E+Space`).

You can also click on the menu with the mouse to open it, as well as clicking on the various menu items to navigate to them.
Click on the already active menu item will execute the command or navigate into the submenu.

Click off the menu to deactivate it.

## Menu annotations

The `…` annotation, like in traditional GUI menus, indicates that the command requires further input.
The `⎘` annotation on a command is specific to VisiData, and means that the command will push a sheet onto the sheet stack, so your data context will change.  You can always return to the previous sheet with `q` (or if you like taking the long way around, the "Sheet»Quit»Top sheet" command in the menu).

## Configuration Options

To make the top menu line disappear (as it looked pre-2.6)

    options.disp_menu = False

The menu can still be activated with `Ctrl+H` or the Alt+ keys as above.  The menu system cannot be entirely disabled.

### Theme options

As with most VisiData display elements, the menu can be altered to taste.  These options are available to change the colors and displayed chars:

- `color_menu`
- `color_menu_active`
- `color_menu_spec`
- `color_menu_help`
- `disp_menu_boxchars`
- `disp_menu_more`
- `disp_menu_input`
- `disp_menu_push`

## Plugin API for adding new menu items

The menu can be extended with additional commands.  See the [plugin API](/docs/api/interface).
