# requirements: mutagen

__name__ = 'vmutagen'
__author__ = 'Saul Pwanson <vd@saul.pw>'
__version__ = '0.1'

import functools

from visidata import *

@functools.lru_cache(None)
def get_mutagen(path):
    import mutagen
    m = mutagen.File(path)
    return m.info


def MutagenColumns():
    for attr in 'bitrate channels encoder_info encoder_settings frame_offset length mode padding protected sample_rate track_gain'.split():
        yield Column(attr, getter=lambda c,r,k=attr: getattr(get_mutagen(r), k))


DirSheet.addCommand('^[m', 'addcol-mutagen', 'for c in MutagenColumns(): addColumn(c)')


vd.addGlobals(globals())
