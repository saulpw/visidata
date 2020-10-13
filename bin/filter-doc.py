#!/usr/bin/python3

import fileinput
import inspect
import visidata

tmpl='''
~~~
    {name}{sign} [ [{sourcepy}:{sourceline}](https://github.com/saulpw/visidata/visidata/blob/develop/visidata/{sourcepy}#{sourceline})]
~~~
{doc}
'''

for line in fileinput.input():
    if line.startswith(':#'):
        objname, funcname = line[2:].strip().split('.')
        func = getattr(getattr(visidata, objname), funcname)
        src = visidata.Path(inspect.getsourcefile(func)).parts[-1]
        print(tmpl.format(
            name=objname+'.'+func.__name__,
            doc=inspect.getdoc(func) or 'XXX',
            sourcepy=src,
            sourceline=inspect.getsourcelines(func)[1],
            sign=inspect.signature(func)))
    else:
        print(line, end='')
