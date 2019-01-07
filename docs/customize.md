- Updated: 2018-12-12
- Version: VisiData 1.5.1

# Customizing VisiData

In VisiData, there is a distinction between global configurations (options/commands) and sheet-specific. Global settings are on default applied to every single sheet in the session. Sheet-specific  ones override global settings for a given **SheetType**.

Examples of **SheetType**s include (but are not limited to):

* **SheetFreqTable** (the command is executable on every [frequency table](/docs/group#frequency));
* **TsvSheet** (option is applied to every loaded .tsv file);
* **ColumnsSheet** (typing selected referenced columns with `g#` can only be done on the **Columns sheet**).

## How to configure VisiData within the current session

Within the application itself:

* Press `zO` to access the **Options sheet** for the current **SheetType**.
* Press `O` to access the global **Options sheet**.

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


---

## How to configure commands

The **.visidatarc** in the user's home directory is plain Python code, and can contain additional commands or key bindings.

Longnames are names given to particular flavours of executable commands for ease of keystroke remapping. For example, the longname `select-row` is assigned to commands which select the current row in a sheet. On default, these are bound to the keystroke `s`.

### Creating command aliases for existing commands

1. Use `zCtrl+H` to open the **Commands Sheet** and discover the [longname]() for the functionality in question.

2. a) To create a global keybinding, add `bindkey(keystroke, longname)` to your **.visidatarc**.
b) To set the binding for a particular sheet type, add `<Sheet>.bindkey(keystroke, longname)` to your **.visidatarc**, where `<Sheet>` is a **SheetType**.

### Creating new commands

Both `globalCommand` and `<Sheet>.addCommand` take the same parameters. At minimum, each command requires a longname and execstr.

~~~
globalCommand(default_keybinding, longname, execstr)
~~~

For example, to define a new global command:

~~~
globalCommand('^D', 'scroll-halfpage-down', ''sheet.topRowIndex += nVisibleRows//2')
~~~

For a sheet-specific command:

~~~
<Sheet>.addCommand('^D', 'scroll-halfpage-down', ''sheet.topRowIndex += nVisibleRows//2')
~~~

where `<Sheet>` is a particular **Sheet Type**.

`execstr` is resolved recursively, so it can be an existing keystroke or `longname` for those that have one.  The last in the chain is `exec()`ed.

---
