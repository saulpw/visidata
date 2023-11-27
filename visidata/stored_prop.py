from functools import wraps
import json
import atexit

from visidata import vd, VisiData, Path

vd.stored_properties = {}

@VisiData.class_api
@classmethod
def stored_property(vdcls, f):
    def _save_on_exit():
        if vd.stored_properties.get(f, None):
            p = Path(vd.options.visidata_dir)/(f.__name__ + '.json')
            with p.open(mode='w', encoding='utf-8') as fp:
                fp.write(json.dumps(vd.stored_properties[f]))

    @property
    @wraps(f)
    def _decorator(*args, **kwargs):
        'Read persisted value from filesystem if available; otherwise call the decorated function to create a new instance.'
        value = vd.stored_properties.get(f, None)
        if value is not None:
            return value

        p = Path(vd.options.visidata_dir)/(f.__name__ + '.json')
        if p.exists():
            value = json.loads(p.open(encoding='utf-8-sig').read())

        if value is None:
            value = f(*args, **kwargs)

        vd.stored_properties[f] = value
        return value

    atexit.register(_save_on_exit)
    setattr(vdcls, f.__name__, _decorator)
    return _decorator
