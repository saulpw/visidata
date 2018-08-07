- Updated: 2018-07-21
- Version: VisiData 1.3

# Customizing VisiData

## How to configure VisiData within the current session

Within the application itself, press `O` to access the **Options sheet**. An option can be edited either by pressing `Enter` or by using [standard editing commands](/man#edit). 

Options can also be passed as arguments through the [commandline](/man#options).  For example

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

Both `option` and `replayableOption` take on the same parameters:

~~~
option(optname, default, helpstr)
~~~

For example, to declare a global option:

~~~
option('num_burgers', 42, 'number of burgers to use')
~~~

To get the value of an option:

~~~
options.num_burgers 
~~~

or

~~~
options['num_burgers']
~~~

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

TODO I NEED A VISIDATARC topic that I can link to for both sections: The contents of **.visidatarc** in the user's home directory (and also the current directory) are `exec()`d on startup.

TODO: explain longnames in a topic

### Creating command aliases for existing commands

1. Use `Ctrl+H` to open the **Commands Sheet** and discover the [longname]() for the functionality in question.

2.
    a) To create a global keybinding, add `bindkey(keystroke, longname)` to your [visidatarc]().
    b) To set the binding for a particular sheet type, add `<Sheet>.bindkey(keystroke, longname)` to your [visidatarc](), where `<Sheet>` is a **SheetType**.

### Creating new commands

Both `globalCommand` and `<Sheet>.addCommand` take the same parameters. At minimum, each command requires a [longname]() and execstr.

~~~
globalCommand(default_keybinding, longname, execstr)
~~~

For example, to define a new global command:

~~~
globalCommand('^D', 'scroll-halfpage-down', ''sheet.topRowIndex += nVisibleRows//2')
~~~

For a sheet-level command:

~~~
<Sheet>.addCommand('^D', 'scroll-halfpage-down', ''sheet.topRowIndex += nVisibleRows//2')
~~~

where `<Sheet>` is a particular **Sheet Type**.

`execstr` is resolved recursively, so it can be an existing keystroke or `longname` for those that have one.  The last in the chain is `exec()`ed.

---
