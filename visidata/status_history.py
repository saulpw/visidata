from visidata import *

command('^P', 'vd.statuses.append(vd.statusHistory[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("statusHistory", vd.statusHistory))', 'open sheet with all previous status messages')

_oldStatus = VisiData.status

def newStatus(self, *args):
    v = _oldStatus(self, *args)
    self.statusHistory.insert(0, v)
    return v

vd().statusHistory = []
VisiData.status = newStatus

