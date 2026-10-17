import locale
import os

from visidata import vd, VisiData


@VisiData.api
def setEnvvar(vd, assignment):
    'Set environment variable from *assignment* (`NAME=value`), and record it on the cmdlogs like a global option.'
    name, sep, value = assignment.partition('=')
    if not name or not sep:
        vd.fail('expected NAME=value')
    os.environ[name] = value
    if name == 'LANG' or name.startswith('LC_'):
        locale.setlocale(locale.LC_ALL, '')
    vd.clearCaches()
    vd.options.add_option_to_cmdlogs('global', '', assignment, longname='set-envvar')


vd.addCommand('', 'set-envvar', 'vd.setEnvvar(input("set env var NAME=value: "))', 'set environment variable', replay=False)

vd.addMenuItems('''
    System > Set environment variable > set-envvar
''')
