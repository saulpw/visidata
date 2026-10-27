import json
import locale
import os

from visidata import vd, VisiData, CompleteKey


@VisiData.api
def setenv(vd, name, value):
    'Set environment variable *name* to *value*, and record it on the cmdlogs like a global option.'
    if not name:
        vd.fail('environment variable name cannot be blank')
    os.environ[name] = value
    if name == 'LANG' or name.startswith('LC_'):
        locale.setlocale(locale.LC_ALL, '')
    vd.clearCaches()
    vd.options.add_option_to_cmdlogs('global', '', json.dumps(dict(name=name, value=value)), longname='set-envvar')


@VisiData.api
def inputEnvvar(vd):
    return vd.inputMultiple(name=dict(prompt='set env var: ', completer=CompleteKey(sorted(os.environ))),
                            value=dict(prompt='to value: '))


vd.addCommand('', 'set-envvar', 'r=inputEnvvar(); vd.setenv(r["name"], r["value"])', 'set environment variable', replay=False)

vd.addMenuItems('''
    System > Set environment variable > set-envvar
''')
