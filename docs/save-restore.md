- Updated: 2018-01-17
- Version: VisiData 0.99

# How to save and replay a VisiData session

This example creates and then uses the file [pivot.vd](https://raw.githubusercontent.com/saulpw/visidata/stable/tests/pivot.vd).

<section id="hero">
    <asciinema-player id="player" poster="npt:0:41" rows=27 src="../casts/save-restore.cast"></asciinema-player>
    <script type="text/javascript" src="/asciinema-player.js"></script>
</section>

To save and restore a session in VisiData:

1. Save the cmdlog using *one* of the following options:

    a. Press `Ctrl+D` to save the cmdlog to a `fn.vd` file.

    *or*

    b. Press `Shift+D` to view the `CommandLog Sheet`, then press `Ctrl+S` and save it with a `.vd` suffix.

2. Press `gq` to quit VisiData.
3. Replay the cmdlog, on the commandline: `vd -p fn.vd`.

# How to replay a cmdlog on a different filename

1. Load the **CommandLog**:

    a. Either open an already saved .vd with `vd foo.vd`.

    *or*

    b. Load the **CommandLog** for the current session with `Shift+D` (commands executed on current sheet only) or `g Shift+D` (commands executed in the entire session).

2. Ensure your cursor is on the **sheet** column. Press `gs` to select all rows, and `gzd` to empty every cell in the **sheet** column.

3. Save the **CommandLog** with `Ctrl+S`.

4. Pass the desired file through the cmdline when replaying:

~~~
vd -p foo.vd data.tsv
~~~

If the **sheet** column in a **CommandLog** is blank, VisiData will refer to the active sheet. Upon startup, that will be the first sheet passed through the commandline. VisiData will load that entire sheet, before replay progresses.

Important, for this to work, all movements between sheets must be explicit within the .vd. This means you need to use `q` or `Ctrl+^` to move between sheets.


---
