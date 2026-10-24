import subprocess
import sys

# subprocess: importing the module rebinds keys for the rest of the process
CHECK = '''
from visidata import vd, Sheet
import visidata.experimental.clipboard_shapes

vs = Sheet('test')
for keys in ['y', 'p']:
    assert vd.bindkeys._get(keys, vs) is None, keys
    assert keys in vd.allPrefixes, keys

for keys, longname in [
    ('y.', 'copy-cell'),
    ('y-', 'copy-row'),
    ('ys-', 'copy-selected'),
    ('ys|', 'copy-cells'),
    ('p.', 'paste-cell'),
    ('p-', 'paste-after'),
    ('ps|', 'setcol-clipboard'),
]:
    assert vd.bindkeys._get(keys, vs) == longname, keys
    assert vs.getCommand(longname), longname
'''


def test_clipboard_shapes_bindings():
    r = subprocess.run([sys.executable, '-c', CHECK], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
