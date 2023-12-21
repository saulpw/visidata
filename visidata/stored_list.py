import json

from visidata import vd, VisiData, Path, AttrDict


@VisiData.api
class StoredList(list):
    'Read existing persisted list from filesystem, and append new elements to .jsonl in .visidata'
    def __init__(self, *args, name:str='', **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    @property
    def path(self):
        vdpath = Path(vd.options.visidata_dir)
        if vdpath.exists():
            return vdpath/(self.name + '.jsonl')

    def reload(self):
        p = self.path
        if not p or not p.exists():
            return

        ret = []
        with p.open(encoding='utf-8-sig') as fp:
            for line in fp:
                value = vd.callNoExceptions(json.loads, line)
                if value is not None:
                    if isinstance(value, dict):
                        value = AttrDict(value)
                    ret.append(value)

        self[:] = ret   # replace without using .append

    def append(self, v):
        super().append(v)

        p = self.path
        if p is None:
            return

        with p.open(encoding='utf-8', mode='a') as fp:
            fp.write(json.dumps(v) + '\n')
