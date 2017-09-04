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

options_cli_skel = '''.It Sy --{cli_optname} Ar {type}
{description} (default '{default}')
'''

options_menu_skel = '''.It Sy "{optname:<18}" No "{default:<16}"
{description} 
'''

with open('{0}-cli.inc'.format(man), 'w') as cliOut:
    with open('{0}-menu.inc'.format(man), 'w') as menuOut:
        opts = vd.baseOptions.keys()

        for optname in opts:
            optname, default, value, desc = vd.baseOptions[optname]
            if optname[:5] in ['color', 'disp_'] or man == 'vdtui':
                options_menu = options_menu_skel.format(optname=optname,type=type(value).__name__,default = str(default), description = desc)
                menuOut.write(options_menu)
            else:
                cliOut.write(options_cli_skel.format(cli_optname=optname.replace('_', '-'),
                                                optname = optname, 
                                                type=type(value).__name__,
                                                 default=default, 
                                                 description=desc))

