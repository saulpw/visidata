from visidata import vd, VisiData, JsonSheet


@VisiData.api
def open_msgpack(vd, p):
    return MsgpackSheet(p.name, source=p)


VisiData.open_msgpackz = VisiData.open_msgpack


class MsgpackSheet(JsonSheet):
    def iterload(self):
        msgpack = vd.importModule('msgpack')
        data = self.source.read_bytes()
        if self.options.filetype == 'msgpackz':
            brotli = vd.importModule('brotli')
            data = brotli.decompress(data)
        yield from msgpack.unpackb(data, raw=False)
