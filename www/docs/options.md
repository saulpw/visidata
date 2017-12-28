- Date: 2017-12-27
- Version: 1.0

# Options

To declare an option:

```
option('num_burgers', 42, 'number of burgers to use')
```

To get the value of an option:

```
options.num_burgers or options['num_burgers']
```

To set the value of an option:

```
options.num_burgers = 13
```

The type of the default is respected, with an `Exception` raised if trying to set with a value that cannot be converted.  (A default value of None will allow any type.)

Option names should use the underscore for word breaks.  On the command-line, underscores must be converted to dashes:

```
$ vd --num-burgers=23
```

The maximum option name length should be 20.

`theme()` should be used instead of `option()` if the option has no effect on the operation of the program, and can be overrided without affecting existing scripts.  The interfaces are identical.  (The implementation is also identical currently, but that may change in the future.)

---
