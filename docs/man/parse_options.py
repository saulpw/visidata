#!/usr/bin/env python3

import sys
import vdtui
import visidata


try:
    man = sys.argv[1]
except:
    man = 'vdtui'

if man == 'vdtui':
    vd = vdtui
elif man in ['vd', 'visidata']:
    vd = visidata
else:
    sys.exit()

print(vd.__version__)
padding = 26

options_cli_skel = '''.It Sy --{cli_optname} Ns = Ns Ar "{type}" No "{default}"
{description}
'''

options_menu_skel = '''.It Sy "{optname:<19}" No "{default}"
{description}
'''

with open('{0}-cli.inc'.format(man), 'w') as cliOut:
    with open('{0}-menu.inc'.format(man), 'w') as menuOut:
        opts = vd.baseOptions.keys()

        colwidth = max((len(optname)+len(str(default))) for optname, default, _, _ in vd.baseOptions.values())
        menuOut.write('.Bl -tag -width %s -compact\n' % ('X'*(colwidth+3)))

        cliwidth = max(padding+len(str(default)) for _, default, _, _ in vd.baseOptions.values())
        cliOut.write('.Bl -tag -width %s -compact\n' % ('X'*(cliwidth+3)))

        for optname in opts:
            optname, default, value, desc = vd.baseOptions[optname]
            if optname[:5] in ['color', 'disp_'] or man == 'vdtui':
                options_menu = options_menu_skel.format(optname=optname,type=type(value).__name__,default = str(default), description = desc)
                menuOut.write(options_menu)
            else:
                cli_optname=optname.replace('_', '-')
                cli_type=type(value).__name__
                optlen = len(cli_optname)+len(cli_type)+1
                cliOut.write(options_cli_skel.format(cli_optname=cli_optname,
                                                optname = optname,
                                                type=cli_type+" "*(padding-optlen),
                                                 default=default,
                                                 description=desc))

        menuOut.write('.El')
        cliOut.write('.El')
