---
eleventyNavigation:
    key: Mouse
    order: 15
Update: 2022-06-19
Version: VisiData v2.8
---

## How to disable the mouse in VisiData?

To disable for all sessions, add to your `~/.visidatarc`:

    options.mouse_interval = 0 # disables the mouse-click
    options.scroll_incr = 0    # disables the scroll wheel

To disable in the current session, press `SPACE`, and type the longname *mouse-disable*.

