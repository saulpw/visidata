---
eleventyNavigation:
    key: Customizing VisiData
    order: 12
Updated: 2023-11-18
Version: VisiData v3.0
---

For a primer on configuring VisiData through setting options, see [jsvine's tutorial](https://jsvine.github.io/intro-to-visidata/advanced/configuring-visidata/).

## How to configure commands {#commands}

The **.visidatarc** in the user's home directory is plain Python code, and can contain additional commands or key bindings.

(Alternatively, since v2.9, VisiData has [XDG support](https://github.com/saulpw/visidata/pull/1420). If `$XDG_CONFIG_HOME` is set and the file `"$XDG_CONFIG_HOME"/visidata/config.py` exists, this will be loaded as the user's default configuration file.)

Longnames are names given to executable commands for ease of keystroke remapping. For example, the longname `select-row` is assigned to commands which select the current row in a sheet. On default, this longname is bound to the keystroke `s`.

From within VisiData, type `z Ctrl+H` to open the **Commands Sheet**. This is a reference for all of the commands available on the current sheet. For a deeper exploration of commands, check out [API reference manual](https://www.visidata.org/docs/api/commands.html).

### Setting/changing keybindings for existing commands

1. Learn the longname for a command. Longnames are usually 2-3 words, separated by hyphens. The first word is usually a verb, and the second usually a noun. When a command is executed, its longname appears in the lower right status, next to its keystroke. Alternatively, you can `z Ctrl+H` to open the **Commands Sheet** and discover the longname for the command in question.

![longname](/docs/assets/longname.png)

2. a) To create a global keybinding, add `bindkey(keystroke, longname)` to your **.visidatarc**.
b) To set the binding for a particular sheet type, add `<Sheet>.bindkey(keystroke, longname)` to your **.visidatarc**, where `<Sheet>` is a **SheetType**.

~~~
Warning: bindings defined in a .visidatarc will overwrite default ones.
~~~

#### Example: Bind `i` to edit-cell globally

In VisiData, pressing `e` enters edit mode for the current cell. Seasoned vim users might prefer to press `i` instead.

1. Open `~/.visidatarc` in an editor.
2. Add the line `TableSheet.bindkey('i', 'edit-cell')` to globally bind the keystroke `i` to the longname `edit-cell`.
3. Launch VisiData, and press `i`.

#### Example: Unbind `i` from addcol-incr globally

If the above instructions are followed, a message will pop up that says "`i` was already bound to `addcol-incr`.

To unbind `i` before binding it:

1. Open `~/.visidatarc` in an editor.
2. Add the line `TableSheet.unbindkey('i')` before any piece of code where it is re-bound.
3. Launch VisiData.


### Creating new commands

At minimum, `<Sheet>.addCommand` requires a longname and execstr.

For example, to define a new command:

~~~
Sheet.addCommand('^D', 'scroll-halfpage-down', 'cursorDown(nScreenRows//2); sheet.topRowIndex += nScreenRows//2')
~~~

Commands and keybindings are set on a particular Sheet Type in the class hierarchy. Use `BaseSheet` for commands which don't need a sheet at all--these will apply to all sheets.  Commands and bindings on more specific sheets will override more generic ones.  `Sheet` is a generic table, `ColumnsSheet` would be for the columns sheet, `FreqTableSheet` for frequency tables, and so on.

### Adding custom aggregators {#aggregators}

Aggregators allow you to gather the rows within a single column, and interpret them using descriptive statistics. VisiData comes pre-loaded with a default set like mean, stdev, and sum.

To add your own custom aggregator `name`, add the following to your `.visidatarc`.

vd.aggregator('name', func, type=float)

Where `func` is a function of the form:

```
def func(list):
    return value
```

The `type` parameter is optional. It allows you to define the default type of the aggregated column.

Here is an example, that adds an aggregator for [numpy's internal rate of return](https://numpy.org/devdocs/reference/generated/numpy.irr.html) module.

```
import numpy as np
vd.aggregator('irr', np.irr, type=float)
```

**Bonus: How to choose which aggregators are columns within the DescribeSheet?**

Any numeric aggregator can be added!

Supply a space-separated list of aggregator names to `options.describe_aggrs` in your .visidatarc.

```
options.describe_aggrs = 'mean stdev irr'
```

### Turning off motd {#motd}

By default, the first time each day that VisiData is used, it downloads a single small file of startup messages.

This network request can be turned off by adding `options.motd_url=''` to your `~/.visidatarc`.

If you do decide to turn it off, we encourage you to [donate](https://www.patreon.com/saulpw/posts) to [support VisiData](https://github.com/sponsors/saulpw).
