---
eleventyNavigation:
    key: Columns
    order: 5
update: 2021-11-01
version: VisiData 2.6
---

## How to manipulate columns

Commands(s)     Operation
------------    -----------
`!`             pins the current column on the left as a key column
 `H`  `L`       slides the current column **one position** to the left/right
`gH` `gL`       slides the current column **all the way** to the left/right of its section

---

## How to hide (remove) and unhide (return) columns

###### How to hide columns

- Press `-` (hyphen) to hide the current column.

**or**

1. Press `Shift+C` on the source sheet to open its **Columns sheet**.
2. Move the cursor right to the **width** column.
3. Move the cursor down to the row which represents the column you wish to hide.
4. Press `e` followed by `0` to set the width for that column to **0**.
5. Press `q` to return to the source sheet.

###### How to unhide columns

1. Press `gv` to unhide all columns on current sheet.

**or**

1. Press `Shift+C` on the source sheet to open its **Columns sheet**.
2. Move the cursor right to the **width** column.
3. Move the cursor down to the row which represents the column you wish to unhide. Currently, that cell should contain the value **0**.
4. Press `e` followed by a *positive number* to set the width.
5. Press `q` to return to the source sheet.

---

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
int       `disp_int_fmt`      `{:.0f}`
float     `disp_float_fmt`    `{:.02f}`
currency  `disp_currency_fmt` `%0.2f`
date      `disp_date_fmt`     `%Y-%m-%d`

Ways to adjust the display formatting:

* The `fmtstr` column on the **Columns Sheet** allows you to specify the formatting for specific columns within that session, without affecting the default for the others.
* The `disp_TYPE_fmt` option can be changed on the **Options Sheet** to set the formatting for all columns of type `TYPE` in that session.
* The `--disp-TYPE-fmt` argument can be passed through the commandline to set the formatting for all columns of type `TYPE` in that session.
* The `options.disp_TYPE_fmt` can be set in the `~/.visidatarc` to change the default formatting for all columns of type `TYPE` for all sessions.

There are several formatting styles offered:

* Formatting that starts with `'%'` (e.g. `%0.2f`) will use [locale.format_string()](https://docs.python.org/3.6/library/locale.html#locale.format_string).
* Otherwise (e.g. `{:.02f}`), formatting will be passed to Python's [string.format()](https://docs.python.org/3/library/string.html#custom-string-formatting).
* Date fmtstr are passed to [strftime](https://strftime.org/).

The default for currency uses `locale.format_string()`. The default for int/float/date use `string.format()`.

###### How to format a specific numeric columns to contain a thousands separator within a session?

1. Set a column to a numeric type by pressing `#` (int), `%` (float), or `$` (currency).
2. Press `Shift+C` to open the **Columns Sheet**.
3. Move to the row referencing the column whose display you wish to format. Move the cursor to the fmtstr column.
4. Type `e` followed by `{:,.0f}` for an `int` type and `{:,.02f}` for a floating point type.

###### How to quickly adjust the precision of a float or date?

1. Ensure the column is typed as numeric column: float (`%`), floatsi (`z%`), dirty float (`$`), or date (`@`).
2. Press `Alt+Plus` or `Alt+Minus` to adjust the precision in the current column.
3. Or, press `Space` and use the longname `setcol-precision-more` or `setcol-precision-less`.

###### How to automatically set the type of a particular column

When loading sheets repeatedly with the same schema, it can be useful to pre-set the column types (and other metadata) in .visidatarc using the `knownCols` attribute on the Sheet class and its subclasses.

For example, to set the "timestamp" column in every sheet to the `date` type:

`Sheet.knownCols.timestamp.type = date`

Or to hide the `nCols` column on the SheetsSheet by default:

`SheetsSheet.knownCols.nCols.width = 0`

###### How to format all date columns as **month/day/year**.

The above method can be used to explicitly set the default `fmtstr` for specifically-named columns.
However, to use a default fmtstr for all date-typed columns, set the `disp_date_fmt` option.  In .visidatarc:

~~~
options.disp_date_fmt = '%m/%d/%Y'
~~~

or pass as a commandline argument:

~~~
vd --disp-date-fmt='%m/%d/%Y'
~~~

or set in the **Options Sheet**.

1. Press `Shift+O` to open the **Options Sheet**.
2. Move the cursor down to the relevant `disp_date_fmt` option.
3. Type `e` followed by `%m/%d/%Y`.

---

###### How to specify a comma decimal separator when typing floating point numbers?

1. Before launching VisiData, set the shell environment variable `LC_NUMERIC` to a locale which interprets commas as decimals. Any European locale should do; an example that works is `en_DK.UTF-8`.
2. Within VisiData, set a column to type `floatlocale` by pressing `Space` followed by `type-floatlocale`.

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
- `*` followed by *regex* and then `Tab` followed by the *replacement* replaces the text matching the *regex* with the contents of *replacement*. *replacement* may include backreferences to capture groups in the regex (`\1` etc).

## How to substitute text in a column

The `*` command can be used to do content transformations of cells. The `g*` variant transforms in-place, instead of creating a new column.

The following example uses [benchmarks.csv](https://raw.githubusercontent.com/saulpw/visidata/stable/sample_data/benchmarks.csv).

**Question** Transform the **SKU** values of *food* to *nutri*.

1. Move cursor to **SKU** column.
2. Press `gs` to select all rows.
3. Press `g*` to replace text in selected rows in current column.
4. Type `food` in the search field.
5. Press `Tab` to go to the replace field, then type `nutri`.
6. Press `Enter` to replace the text.

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
- **`curcol`**: evaluate to the typed value of this row in the column that the cursor was on at the time that the expression column was added.
- **`cursorCol`**: evaluate to the typed value of this row for the column the cursor is on. Changes as the cursor moves for `=`. Uses the column from the time the calculation was made for `g=`, `gz=`, and `z=`.

Additional attributes can be added to sheets and columns.

`col` deliberately returns a Column object, but any other Column object is interpreted as the value within that column for the same row. For example, both `curcol` and `cursorCol` return values, not the object itself.


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
2. Type `=` followed by `curcol.casefold()`.
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
