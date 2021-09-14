---
eleventyNavigation:
  key: Options
  order: 99
Date: 2021-09-13
Version: 2.6
---


## Options

To declare an option:

```
vd.option('num_burgers', 42, 'number of burgers to use')
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

Option names should use the underscore for word breaks.  On the command-line, underscores can be converted to dashes:

```
$ vd --num-burgers=23
```

The maximum option name length should be 20.

---
