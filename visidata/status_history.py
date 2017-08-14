from .vdtui import *

command('^P', 'vd.statuses.append(vd.statusHistory[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("statusHistory", vd.statusHistory))', 'open sheet with all previous status messages')

