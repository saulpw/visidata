import locale
import os

from visidata import vd, VisiData


@VisiData.api
def setEnvvar(vd, name, value):
    'Set an environment variable and record it for replay, refreshing the locale if needed.'
    is_locale = name == 'LANG' or name.startswith('LC_')
    previous_value = os.environ.get(name)
    previous_locale = locale.setlocale(locale.LC_ALL) if is_locale else None
    try:
        os.environ[name] = value
    except (ValueError, OSError):
        vd.fail('invalid environment variable assignment')

    if is_locale:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except locale.Error:
            if previous_value is None:
                del os.environ[name]
            else:
                os.environ[name] = previous_value
            locale.setlocale(locale.LC_ALL, previous_locale)
            vd.fail(f'cannot apply locale from `{name}`')

    vd.clearCaches()
    assignment = f'{name}={value}'
    if vd.activeCommand and vd.activeCommand.longname == 'set-envvar':
        vd.activeCommand.input = assignment
    else:
        vd.cmdlog.add_global(vd.cmdlog.newRow(longname='set-envvar',
                    input=assignment, undofuncs=[]))


@VisiData.api
def set_envvar(vd, assignment):
    name, sep, value = assignment.partition('=')
    sep or vd.fail('expected `NAME=value`')
    vd.setEnvvar(name, value)


vd.addCommand('', 'set-envvar', 'vd.set_envvar(input("set env var NAME=value: "))',
              'set environment variable and record it for replay')

vd.addMenuItems('''
    System > Set environment variable > set-envvar
''')
