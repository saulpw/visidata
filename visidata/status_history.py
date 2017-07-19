from visidata import *

command('^P', 'vd.statuses.append(vd.statusHistory[0])', 'show last status message again')
command('g^P', 'vd.push(TextSheet("statusHistory", vd.statusHistory))', 'open sheet with all previous status messages')


def newStatus(self, *args):
    v = _oldStatus(*args)
    self.statusHistory.insert(0, v)
    return v

_oldStatus = vd().status
vd().statusHistory = []
vd().status = lambda *args,vd=vd(): newStatus(vd, *args)

