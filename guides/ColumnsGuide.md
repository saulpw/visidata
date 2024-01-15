## Key columns

TODO

- {help.commands.key_col}

## Change column order

- {help.commands.slide_left}
- {help.commands.slide_right}
- {help.commands.slide_leftmost}
- {help.commands.slide_rightmost}
- {help.commands.slide_left_n}
- {help.commands.slide_right_n}

## Hide and unhide columns

- {help.commands.hide_col}
- {help.commands.unhide_cols}

### via the Columns Sheet

1. {help.commands.columns_sheet}.
1. {help.commands.go_right} to the `width` column.
1. {help.commands.go_down} to the source column.
4. {help.commands.edit_cell} the width to `0` to hide the column; or any positive number to set the width.
5. {help.commands.quit_sheet} and return to the source sheet.


## How to specify column types

Command    Type
--------- --------
` ~`      string
` #`      int
` %`      float
` $`      currency
` @`      date
`z#`      vlen
`z~`      anytype

Columns usually begin as untyped (`anytype`). Errors when working with numerical or datetime data is often due to values being considered as strings, and the problem is solved by setting the correct type.

The `float` type uses Python's builtin `float()` constructor to parse the string, and it parses by using the decimal separator.

The `currency` type is a bit of a misnomer. It filters out any non-numeric characters, and then parses the remainder of the cell value as a float.
The reasons to prefer using `float` over `currency`, is performance (it is quite a bit slower than native parsing with `float`), or if any non-float characters should get reported as an error.

The `date` type parses dates into ISO8601 format. Those columns can then be used in mathematical calculations, and the calculations are interpreted for dates. E.g. 2020-01-01 + 1, is 2020-01-02.

The `vlen` type formats the cell value to the length of the content. For example, if the cell content is a list of length 3, then when `vlen` typed it will display a value of 3.

There is also the `floatlocale` type, which uses Python's `locale.atof` to parse the Column values. With `floatlocale`, you can set the `LC_NUMERIC` environment variable appropriately (before launching VisiData), such that `atof()` will parse the number based on your locale setting. There is a `type-floatlocale` command, which is unbound by default, because parsing this way is significantly slower than using the builtin float type.

If you need locale-specific float parsing regularly, you may want to [rebind](/docs/customize) `%` or `z%` (or maybe some other keystroke) to `type-floatlocale` instead.

The following example uses the file [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).

<div class="asciicast">
    <asciinema-player id="player-types" poster="npt:0:20" rows=27 src="../casts/types.cast"></asciinema-player>
    <script type="text/javascript" src="/asciinema-player.js"></script>
</div>

###### How to batch specify column types for more than one column

1. Press `Shift+C` to open the **Columns sheet**.
2. Press `s` or `t` to select the rows referencing the columns you wish to type.
3. Type `g` followed by the any of the above typing keystrokes to set the type for all selected columns on the source sheet.

---

## How to format columns

**Note**: Un-typed file formats, like tsvs and csvs, will save as they are displayed.

Some types have an option for their default display formatting.

Type      Option            Default
--------- ----------------  --------
int       disp_int_fmt      {:.0f}
float     disp_float_fmt    {:.02f}
currency  disp_currency_fmt %0.2f
date      disp_date_fmt     %Y-%m-%d

Ways to adjust the display formatting:

* The `fmtstr` column on the **Columns Sheet** allows you to specify the formatting for specific columns within that session, without affecting the default for the others.
* The `disp_TYPE_fmt` option can be changed on the **Options Sheet** to set the formatting for all columns of type `TYPE` in that session.
* The `--disp-TYPE-fmt` argument can be passed through the commandline to set the formatting for all columns of type `TYPE` in that session.
* The `options.disp_TYPE_fmt` can be set in the `~/.visidatarc` to change the default formatting for all columns of type `TYPE` for all sessions.

There are several formatting styles offered:

* Formatting that starts with `'%'` (e.g. *%0.2f*) will use [locale.format_string()](https://docs.python.org/3.6/library/locale.html#locale.format_string).
* Otherwise (e.g. *{:.02f}*), formatting will be passed to Python's [string.format()](https://docs.python.org/3/library/string.html#custom-string-formatting).
* Date fmtstr are passed to [strftime](https://strftime.org/).

The default for currency uses `locale.format_string()`. The default for int/float/date use `string.format()`.

###### How to format a specific numeric columns to contain a thousands separator within a session?

1. Set a column to a numeric type by pressing `#` (int), `%` (float), or `$` (currency).
2. Press `Shift+C` to open the **Columns Sheet**.
3. Move to the row referencing the column whose display you wish to format. Move the cursor to the fmtstr column.
4. Type `e` followed by *{:,.0f}* for an `int` type and *{:,.02f}* for a floating point type.

###### How to quickly adjust the precision of a float or date?

1. Ensure the column is either typed as a float (`%`), floatsi, currency (`$`), or date (`@`).
2. Press `SPACE` and type the longnames `setcol-precision-more` or `setcol-precision-less` to adjust the precision in the current column.

[Bind the longnames to keys](https://www.visidata.org/docs/customize/), if using these commands frequently.

###### How to set all date columns to be **month/day/year**.

The default can be set in a `~/.visidatarc`.

~~~
options.disp_date_fmt = '%m/%d/%Y'
~~~

or passed through the commandline

~~~
vd --disp-date-fmt='%m/%d/%Y'
~~~

or set in the **Options Sheet**.

1. Press `Shift+O` to open the **Options Sheet**.
2. Move the cursor down to the relevant *disp_date_fmt* option.
3. Type `e` followed by *%m/%d/%Y*.

---

###### How to specify a comma decimal separator when typing floating point numbers?

1. Before launching VisiData, set the shell environment variable `LC_NUMERIC` to a locale which interprets commas as decimals. Any European locale should do; an example that works is `en_DK.UTF-8`.
2. Within VisiData, set a column to type `floatlocale` by pressing `Space` followed by *type-floatlocale*.

Note that `type-floatlocale` is significantly slower than `type-float`. However, if you wish to replace the current binding for `type-float` with `type-floatlocale`, add to your `~/.visidatarc`:

~~~
Sheet.unbindkey('%')
Sheet.bindkey('%', 'type-floatlocale')
~~~

or if you never use `type-floatsi`, you can do


~~~
Sheet.unbindkey('z%')
Sheet.bindkey('z%', 'type-floatlocale')
~~~

## How to split a column

Python regular expressions provide more finetuned column splitting. The following example
uses the commands for column splitting and transformation with [xd/puzzles.tsv](http://xd.saul.pw/xd-metadata.zip).

<div class="asciicast">
    <asciinema-player id="player-split-regex" poster="npt:0:20" rows=27 src="../casts/split-regex.cast"></asciinema-player>
</div>

###

- `:` adds new columns derived from splitting the current column at positions defined by a *regex pattern*. `options.default_sample_size` (default: 100) rows around the cursor will be used to determine the number of columns that will be created.
- `;` adds new columns derived from pulling the contents of the current column which match the *regex within capture groups*. The new columns are named using the capture group index, or if named capture groups are used, the capture group names. This command uses the `options.default_sample_size` (default:100) rows around the cursor as sample rows.
- `*` followed by *regex*`/`*substring* replaces the text which matches the capture groups in *regex* with the contents of *substring*. *substring* may include backreferences (*\1* etc).

## [How do I substitute text in my column]

The `*` command can be used to do content transformations of cells. The `g*` variant transforms in-place, instead of creating a new column.

The following example uses [benchmarks.csv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/benchmarks.csv).

**Question** Transform the **SKU** values of *food* to *nutri*.

1. Move cursor to **SKU** column.
2. Press `gs` to select all rows.
3. Type `g*` followed by *food/nutri*.

- tests/transform-cols.vd


---

## [How to expand columns that contain nested data](#expand) {#expand}

If a column includes container data such as JSON objects or arrays, the `(` family of commands can expand the child values into top-level columns:

Command       Operation
---------     --------
`  (`         expand _current_ column
` g(`         expand _all visible_ columns fully
` z(`         expand _current_ column to a specific depth (prompt for input)
`gz(`         expand _all visible_ columns to a specific depth (prompt for input)
`  )`         contract (unexpand) the current column
` zM`         expand _current_ column row-wise within that column

The following demo shows `(` commands applied to this data:

~~~
[
    [ "short", "array" ],
    [ "slightly", "longer", "array" ],
    { "nested": "data" },
    { "more": { "deeply": { "nested": "data" } } }
]
~~~

<div class="asciicast">
    <asciinema-player id="player-expand-cols" poster="npt:0:20" rows=13 src="../casts/expand-cols.cast"></asciinema-player>
</div>

Note that by default the expansion logic will look for nested columns in **up to** `options.default_sample_size` (Default: 100) **rows surrounding the cursor**. This behavior can be controlled by adjusting `default_sample_size` in the **Options Sheet**, or setting `options.default_sample_size` in the `~/.visidatarc` file.

---

## [How to create derivative columns](#derived) {#derived}

The `=` command takes a Python expression as input and creates a new column, where each cell evaluates the expression in the context of its row.

These variables and functions are available in the scope of an expression:

- **Column names** evaluate to the typed value of the cell in the named column for the same row.
- **`vd`** attributes and methods; use `Ctrl+X vd` to view the vd object, or [see the API]().
- **`Sheet`** attributes and methods; use `g Ctrl+Y` to view the sheet object (or see the API).
- **Global** functions and variables (add your own in your .visidatarc).
- **modules** that have been `import`ed in Python
  - if you need a module that hasn't already been imported at runtime, use `g Ctrl+X import <modname>`.

- **`sheet`**: the current sheet (a TableSheet object)
- **`col`**: the current column (as a Column object; use for Column metadata)
- **`row`**: the current row (a Python object of the internal rowtype)
- **curcol**: evaluate to the typed value of this row in the column that the cursor was on at the time that the expression column was added.
- **cursorCol**: evaluate to the typed value of this row for the column the cursor is on. Changes as the cursor moves for `=`. Uses the column from the time the calculation was made for `g=`, `gz=`, and `z=`.

Additional attributes can be added to sheets and columns.

`col` deliberately returns a Column object, but any other Column object is interpreted as the value within that column for the same row. For example, both `curcol` and `cursorcol` return values, not the object itself.


For example, this customizes addcol-expr to set the `curcol` attribute on the new ExprColumn to a snapshot of the current cursor column (at the time the expression column is added):

```
Sheet.addCommand('=', 'addcol-expr', 'addColumnAtCursor(ExprColumn(inputExpr("new column expr="), curcol=cursorCol))', 'create
 new column from Python expression, with column names as variables')
```

Then, an expression can use `curcol` as though it referred to the value in the saved column.

`Tab` autocompletion when inputting an expression will cycle through valid column names only.

The following examples use the file [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).

**Question** On which days have we sold more than 10 **Item**s?

1. Scroll to the **Units** column. Set the type of the **Units** column by pressing `#` (int).
2. Type `=` followed by `Units > 10`. A new column will be created. The cells in this column will contain the value **True** in rows where the number of **Units** are greater than 10 and **False** otherwise.
3. Move to the new derived column.
4. Type `|` followed by `True` to select all rows where there were more than 10 **Units** sold.
5. Press `"` to open a duplicate sheet with only those selected rows.

**Question** I have a dataset with separate columns for **Year**, **Month** and **Day**. How can I concatenate them into a single date column?

1. Type `=` followed by `Year + '-' + Month + '-' + Day`.
2. Set the type of the new derived column by pressing `@` (date).
3. Type `^` followed by `Date` to rename the column to **Date**.

**Question** I have a dataset with **Date** column that is missing a prefix of '2020-'. How do I add it to the **Date** column?

When using `=`, and wanting to reference the current column, we recommend using `curcol`. When using `g=`, `gz=`, and `z=`, we recommend cursorCol. `=`, unlike the others, is dynamic and changes with adjustment of underlying values, which means it will change along with the movement of the cursor (tracked by `cursorCol`). `curcol` is a special attribute of a new **ExprColumn**, which remembers the cursorCol at the time of creation.

1. Move the cursor to **Date**.
2. Type `g=` followed by *f"2020-{cursorCol}"*.

**Question** I have a dataset with **file names**. How do I create a new column with the **file names** lower cased?

1. Move the cursor to **file names** column.
2. Type `=` followed by **curcol.casefold()**.
3. Move to the newly created column, and rename it with `^`, followed by the desired name.

---

## How to configure multiple columns

Properties of columns on the source sheet can be changed by using [standard editing commands](/man#edit) on its **Columns sheet** (accessed with `Shift+C`). In particular, it facilitates the selection of multiple columns, followed by utilising one of the `g`-prefixed commands to modify all of them.

For a full list of available commands, see the [man page](/man#columns). Some example workflows follow.

The following examples use the file [sample.tsv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/sample.tsv).

###### How to set multiple statistical aggregators

**Question** What is the average daily revenue from sales of each **Item**?

1. Set the type of the **Units** column by pressing `#` (int).
2. Set the type of the **Total** column by pressing `%` (float).
3. Press `Shift+C` to open the **Columns sheet**.
4. Press `s` or `t` on the rows referencing the source sheet **Units** column and the **Total** column to select them.
5. Type `g+` followed by `avg` to add a **avg** statistical aggregator to the selected rows.
6. Press `q` to exit and return to the source sheet.
7. Scroll to the **Item** column. Press `Shift+F` to open the **Frequency table**.

**Question** What are the daily average and sum total number of **Units** sold for each **Item**?

1. Press `Shift+C` to open the **Columns sheet**.
2. Move the cursor to the row referencing the source sheet **Units** column.

    a. Press `s` or `t` to select it.
    b. Set the type for the source sheet **Units** columns by pressing `g#` (int).
    c. Move the cursor to the **aggregators** column.
    d. Type `e` to enter edit mode, followed by *sum avg*.

3. Press `q` to exit and return to the source sheet.
4. Move the cursor to the **Item** column. Press `Shift+F` to open the **Frequency table**.

---
