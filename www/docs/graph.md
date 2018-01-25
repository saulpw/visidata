- Update: 2018-01-22
- Version: VisiData 1.0

# Drawing graphs

Graphs in VisiData can be used to visualise the relationship between numeric dependent variables vs a numeric independent variable. Optionally, a second independent variable, which is categorical,  adds an additional colored scatter plot for each category.

This example uses the file [StatusPR.csv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/StatusPR.csv).

<section id="hero">
    <asciinema-player id="player" poster="npt:0:30" rows=27 src="../casts/pivot-graphs.cast"></asciinema-player>
    <script type="text/javascript" src="/asciinema-player.js"></script>
</section>

---

## How to graph a single column

1. Press `!` to set a column as the x-axis. This column must be numeric.
2. Set that column to a numeric type by pressing `#` (int), `%` (float), `$` (currency), or `@` (date).
3. Optional: Press `!` on a categorical key column to add it as an additional independent variable.
4. Set the type of the column you wish to set as the dependent variable with a numeric type.
5. Press `.` (dot=plot) on that column.

---

## How to graph multiple columns

1. Press `!` to set a column as the x-axis. This column must be numeric.
2. Set that column to a numeric type.
3. Optinal: Press `!` on a categorical key column to add it as an additional independent variable.
4. Type all of the columns you wish to set as the dependent variables with a numeric type.
5. Press `-` (dash) to hide any numeric columns you don't wish graphed.
6. Press `g.`.

---

##How to interact with graphs

###### With the keyboard

Command(s)          Operation
----------          ----------
`1`-`9`             toggles display of each scatterplot layer
`h`  `j`  `k`  `l`  moves the cursor
`H`  `J`  `K`  `L`  expands and shrinks the cursor
`+`  `-`            increases/decreases the zoomlevel, centered on the cursor
`zz`                zooms into the cursor
`_` (underscore)    zooms to fit the full extent
 `s`   `t`   `u`    selects/toggles/unselects rows on the source sheet contained within the cursor
`gs`  `gt`  `gu`    selects/toggles/unselects rows visible on the screen
 `Enter`            opens sheet of source rows contained within the cursor
`gEnter`            opens sheet of source rows which are visible on screen
`w`                 toggles the visibility of graph labels

###### With the mouse

Command                 Operation
-------                 -----------
Left-click and drag     sets the cursor
Right-click and drag    scrolls
Scroll-wheel            zooms in/out

---
