from visidata import *

command('^P', 'vd.statuses.append(vd.statusHistory[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("statusHistory", vd.statusHistory))', 'open sheet with all previous status messages')

_oldStatus = VisiData.status

def newStatus(self, s):
    self.statusHistory.insert(0, str(s))
    return _oldStatus(self, s)

vd().statusHistory = []
VisiData.status = newStatus

