from visidata import *


def diskcache(fn, cachesecs):
    'cache return value of decorated func to ~/.visidata/fn for cachesecs'
    def cachemaker(func):
        @functools.lru_cache()
        def cachethis(*args, **kwargs):
            cachedir = Path('~/.visidata/')
            if not cachedir.exists():
                os.mkdir(cachedir.resolve())

            assert cachedir.is_dir(), cachedir

            p = Path('~/.visidata/' + fn)
            if p.exists():
                secs = time.time() - p.stat().st_mtime
                if secs < cachesecs:
                    return p.read_text()

            ret = func(*args, **kwargs)
            with p.open_text(mode='w') as fpout:
                fpout.write(ret)
            return ret
        return cachethis
    return cachemaker
