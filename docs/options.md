# A minimalistic internal options framework in Python

Pros:

* implementation in very few lines of code
* declaration and usage are very convenient
* options are automatically typed (and Exception raised on set if conversion fails)

##

```
base_options = collections.OrderedDict()

class configbool:
    def __init__(self, v):
        if isinstance(v, str):
            self.val = v and (v[0].upper() not in "0FN")
        else:
            self.val = bool(v)

    def __bool__(self):
        return self.val

    def __str__(self):
        return str(self.val)

def option(name, default, helpstr=''):
    if isinstance(default, bool):
        default = configbool(default)

    base_options[name] = [name, default, default, helpstr]

class OptionsObject:
    'minimalist options framework'
    def __init__(self, d):
        object.__setattr__(self, '_opts', d)

    def __getattr__(self, k):
        name, value, default, helpstr = self._opts[k]
        return value

    def __setattr__(self, k, v):
        self.__setitem__(k, v)

    def __setitem__(self, k, v):
        if k not in self._opts:
            raise Exception('no such option "%s"' % k)
        self._opts[k][1] = type(self._opts[k][1])(v)

options = OptionsObject(base_options)
```

Now we have a generic options framework.  To define an option, call this at the top-level:

```option('foo', 100, 'number of times to foo')```

To get the value of an option, just use `options.foo` or `options['foo']`.

To set an option programmatically, do `options.foo = 200` (after the `option()` has been defined).

Finally, this options framework allows automatic generation of command-line arguments from the options:

```
    parser = argparse.ArgumentParser(description=__doc__)

    for optname, v in base_options.items():
        name, optval, defaultval, helpstr = v
        action = 'store_true' if optval is False else 'store'
        parser.add_argument('--' + optname.replace('_', '-'), action=action, dest=optname, default=optval, help=helpstr)

    args = parser.parse_args()

    for optname, optval in vars(args).items():
        if optname not in ['inputs']:  # any options not defined with option()
            options[optname] = optval  # auto-converts to type of default
```



