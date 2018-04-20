#!/usr/bin/env python3

# Usage: $0 visidata-cli.inc visidata-opts.inc

import sys
import vdtui
import visidata


fncli, fnopts = sys.argv[1:]

print(visidata.__version_info__)
padding = 26

options_cli_skel = '''.It Sy --{cli_optname} Ns = Ns Ar "{type}" No "{default}"
{description}
'''

options_menu_skel = '''.It Sy "{optname:<19}" No "{default}"
{description}
'''

visidata.options.plot_colors = ''

with open(fncli, 'w') as cliOut:
    with open(fnopts, 'w') as menuOut:
        opts = visidata.baseOptions.keys()

        widestoptwidth, widestopt = sorted((len(opt.name)+len(str(opt.default)), opt.name) for opt in visidata.baseOptions.values())[-1]
        print('widest option+default is "%s", width %d' % (widestopt, widestoptwidth))
        menuOut.write('.Bl -tag -width %s -compact\n' % ('X'*(widestoptwidth+3)))

        cliwidth = max(padding+len(str(opt.default)) for opt in visidata.baseOptions.values())
        cliOut.write('.Bl -tag -width %s -compact\n' % ('X'*(cliwidth+3)))

        for optname in opts:
            opt = visidata.baseOptions[optname]
            if opt.name[:5] in ['color', 'disp_']:
                options_menu = options_menu_skel.format(optname=opt.name,type=type(opt.value).__name__,default = str(opt.default), description = opt.helpstr)
                menuOut.write(options_menu)
            else:
                cli_optname=opt.name.replace('_', '-')
                cli_type=type(opt.value).__name__
                optlen = len(cli_optname)+len(cli_type)+1
                cliOut.write(options_cli_skel.format(cli_optname=cli_optname,
                                                optname = opt.name,
                                                type=cli_type+" "*(padding-optlen),
                                                 default=opt.default,
                                                 description=opt.helpstr))

        menuOut.write('.El')
        cliOut.write('.El')
