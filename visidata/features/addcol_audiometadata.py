# requirements: mutagen

import functools

from visidata import vd, Column, AttrColumn, DirSheet


@functools.lru_cache(None)
def get_mutagen_info(path):
    mutagen = vd.importExternal('mutagen')
    m = mutagen.File(path)
    return m.info


class MutagenColumn(AttrColumn):
    def calcValue(self, r):
        md = get_mutagen_info(r)
        return getattr(md, self.expr, None)


@DirSheet.api
def audiometadata_columns(sheet):
    return [
        Column('audio_info', width=0, getter=lambda c,r: get_mutagen_info(r)),
        MutagenColumn('bitrate'),
        MutagenColumn('channels'),
        MutagenColumn('encoder_info'),
        MutagenColumn('encoder_settings'),
        MutagenColumn('frame_offset'),
        MutagenColumn('length'),
        MutagenColumn('mode'),
        MutagenColumn('padding'),
        MutagenColumn('protected'),
        MutagenColumn('sample_rate'),
        MutagenColumn('track_gain'),
    ]


DirSheet.addCommand('', 'addcol-audiometadata', 'addColumn(*audiometadata_columns())', 'add metadata columns for audio files (MP3, FLAC, Ogg, etc)')


vd.addMenuItems('Column > Add column > audio metadata > addcol-audiometadata')
