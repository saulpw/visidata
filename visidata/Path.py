
# should be compatible with Python 3.4 pathlib.Path.
# transition to pathlib if/when we adopt async from 3.5.
# marginal desire to maintain compatibility with older Python versions.

import os
import os.path


class Path:
    def __init__(self, fqpn):
        self.fqpn = fqpn
        self.name = os.path.split(fqpn)[-1]
        self.suffix = os.path.splitext(self.name)[1][1:]

    def read_text(self, encoding=None, errors=None):
        with open(self.resolve(), encoding=encoding, errors=errors) as fp:
            return fp.read()

    def read_bytes(self):
        with open(self.resolve(), 'rb') as fp:
            return fp.read()

    def is_dir(self):
        return os.path.isdir(self.resolve())

    def iterdir(self):
        return [self.parent] + [Path(os.path.join(self.fqpn, f)) for f in os.listdir(self.resolve())]

    def stat(self):
        return os.stat(self.resolve())

    def resolve(self):
        return os.path.expandvars(os.path.expanduser(self.fqpn))

    @property
    def parent(self):
        return Path(self.fqpn + "/..")

    def __str__(self):
        return self.fqpn
