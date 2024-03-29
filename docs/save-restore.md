---
eleventyNavigation:
    key: Save and Restore
    order: 11
Updated: 2018-01-17
Version: VisiData 0.99
---


## How to save and replay a VisiData session

This example creates and then uses the file [pivot.vdj](https://raw.githubusercontent.com/saulpw/visidata/stable/tests/pivot.vdj).

<section id="hero">
    <asciinema-player id="player" poster="npt:0:41" rows=27 src="../casts/save-restore.cast"></asciinema-player>
    <script type="text/javascript" src="/asciinema-player.js"></script>
</section>

To save and restore a session in VisiData:

1. Save the cmdlog using *one* of the following options:

    a. Press `Ctrl+D` to save the cmdlog to a `fn.vdj` file.

    *or*

    b. Press `Shift+D` to view the `CommandLog Sheet`, then press `Ctrl+S` and save it with a `.vdj` suffix.

2. Press `gq` to quit VisiData.
3. Replay the cmdlog, on the commandline: `vd -p fn.vdj`.

---
