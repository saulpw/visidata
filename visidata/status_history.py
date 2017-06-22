from visidata import *

command('^P', 'vd.statuses.append(vd.status_history[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("status_history", vd.status_history))', 'open sheet with all previous status messages')

_old_status = VisiData.status

def new_status(self, s):
    self.status_history.insert(0, str(s))
    return _old_status(self, s)

vd().status_history = []
VisiData.status = new_status

