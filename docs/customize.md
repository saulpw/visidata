- Updated: 2019-11-02
- Version: VisiData v2.-1

# Customizing VisiData

In VisiData, there is a distinction between global configurations (options/commands) and sheet-specific. Global settings are on default applied to every single sheet in the session. Sheet-specific  ones override global settings for a given **SheetType**.

Examples of **SheetType**s include (but are not limited to):

* **FreqTableSheet** (the command is executable on every [frequency table](/docs/group#frequency));
* **TsvSheet** (option is applied to every loaded .tsv file);
* **ColumnsSheet** (typing selected referenced columns with `g#` can only be done on the **Columns sheet**).

## How to configure VisiData within the current session

Within the application itself:

* Press `z Shift+O` to access the **Options sheet** for the current **SheetType**.
* Press `Shift+O` to access the global **Options sheet**.

An option can be edited either by pressing `Enter` or by using [standard editing commands](/man#edit).

Global options can also be passed as arguments through the [commandline](/man#options).  For example

~~~
vd --skip 2
~~~

or

~~~
vd --skip=2
~~~

---

## How to have setting configurations persist

The contents of **.visidatarc** in the user's home directory (and also the current directory) are `exec()`d on startup. Options set through the command-line or **Options Sheet** will override those set in **.visidatarc**.

To set the global value of an option:

~~~
options.num_burgers = 13
~~~

The type of the default is respected. An **Exception** will be raised if the option is later set with a value that cannot be converted.  (A default value of **None** will allow any type.)

Option names should use the underscore for word breaks. On the command-line, underscores must be converted to dashes:

~~~
$ vd --num-burgers=23
~~~

The maximum option name length should be 20.

`theme()` should be used instead of `option()` if the option has no effect on the operation of the program, and can be overrided without affecting existing scripts.  The interfaces are identical.  (The implementation is also identical currently, but that may change in the future.)

This Python script can be used to generate a sample `~/.visidatarc`, with all of the option defaults:

~~~
from visidata import options

for optname, val in sorted(options().items()):
    val = repr(val)
    helpstr = options._get(optname, 'global').helpstr
    print(f'options.{optname:25s} = {val:10s}  # {helpstr}')
~~~

::::: {.announce}

---
#### Extra Python aid

To run the above code, place it in a file named vdrc.py. Then run it by typing

```
python3 vdrc.py
```

in the terminal.

#### Extra terminal aid

You can stdout redirection to place the output in a file:

```
python3 vdrc.py > ~/.visidatarc-template
```

Careful, `>` will overwrite files they are directing to. `>>` will append to the file.

---

:::::

---

## How to configure commands {#commands}

The **.visidatarc** in the user's home directory is plain Python code, and can contain additional commands or key bindings.

Longnames are names given to particular flavours of executable commands for ease of keystroke remapping. For example, the longname `select-row` is assigned to commands which select the current row in a sheet. On default, this longname is bound to the keystroke `s`.

From within VisiData, type `z Ctrl+H` to open the **Commands Sheet**. This is a reference for all of the commands available on the current sheet. For a deeper exploration of commands, check out [the book of VisiData](https://github.com/saulpw/visidata-book/blob/master/commands.md).

### Setting/changing keybindings for existing commands

1. Use `z Ctrl+H` to open the **Commands Sheet** and discover the [longname]() for the functionality in question.

2. a) To create a global keybinding, add `bindkey(keystroke, longname)` to your **.visidatarc**.
b) To set the binding for a particular sheet type, add `<Sheet>.bindkey(keystroke, longname)` to your **.visidatarc**, where `<Sheet>` is a **SheetType**.

~~~
Warning: bindings defined in a .visidatarc will overwrite default ones.
~~~

#### Example: Bind `i` to edit-cell globally

In VisiData, pressing `e` enters edit mode for the current cell. Seasoned vim users might prefer to press `i` instead.

1. Open `~/.visidatarc` in an editor.
2. Add the line `bindkey('i', 'edit-cell')` to globally bind the keystroke `i` to the longname `edit-cell`.
3. Launch VisiData, and press `i`.


### Creating new commands

Both `globalCommand` and `<Sheet>.addCommand` take the same parameters. At minimum, each command requires a longname and execstr.

~~~
globalCommand(default_keybinding, longname, execstr)
~~~

For example, to define a new global command:

~~~
globalCommand('^D', 'scroll-halfpage-down', 'cursorDown(nScreenRows//2); sheet.topRowIndex += nScreenRows//2')
~~~

For a sheet-specific command:

~~~
<Sheet>.addCommand('^D', 'scroll-halfpage-down', 'cursorDown(nScreenRows//2); sheet.topRowIndex += nScreenRows//2')
~~~

where `<Sheet>` is a particular **Sheet Type**.

Note that sheet-specific commands trump globally set commands for keybindings.

`globalCommand` is primarily for commands which don't need a sheet at all. In most cases, commands should be on `Sheet` or a further specialised **Sheet Type**.

~~~
Sheet.addCommand('^D', 'scroll-halfpage-down', 'cursorDown(nScreenRows//2); sheet.topRowIndex += nScreenRows//2')
~~~

`execstr` is resolved recursively, so it can be an existing keystroke or `longname` for those that have one.  The last in the chain is `exec()`ed.

---

### Adding custom aggregators

Aggregators allow you to gather the rows within a single column, and interpret them using descriptive statistics. VisiData comes pre-loaded with a default set like mean, stdev, and sum.

To add your own custom aggregator `name`, add the following to your `.visidatarc`.

aggregator('name', func, type=float)

Where `func` is a function of the form:

```
def func(list):
    return value
```

The `type` parameter is optional. It allows you to define the default type of the aggregated column.

Here is an example, that adds an aggregator for [numpy's internal rate of return](https://numpy.org/devdocs/reference/generated/numpy.irr.html) module.

```
import numpy as np
aggregator('irr', np.irr, type=float)
```

**Bonus: How to choose which aggregators are columns within the DescribeSheet?**

Any numeric aggregator can be added!

Supply a space-separated list of aggreagator names to `options.describe_aggr` in your .visidatarc.

```
options.describe_aggrs = 'mean stdev irr'
```
