from visidata import vd, BaseSheet, Column
from visidata.pyobj import PythonSheet, PyobjSheet


# rowdef: Distribution object from importlib.metadata
class PythonPackagesSheet(PythonSheet):
    'Sheet displaying installed Python packages via importlib.metadata.distributions()'
    rowtype = 'packages'
    columns = [
        Column('name', getter=lambda c,r: r.name),
        Column('version', getter=lambda c,r: r.version),
        Column('summary', getter=lambda c,r: r.metadata.get('Summary', '')),
        Column('author', getter=lambda c,r: r.metadata.get('Author', '')),
        Column('license', getter=lambda c,r: r.metadata.get('License', '')),
        Column('location', getter=lambda c,r: str(r._path.parent) if hasattr(r, '_path') and r._path else ''),
        Column('home_page', getter=lambda c,r: r.metadata.get('Home-page', '')),
    ]
    nKeys = 1

    def reload(self):
        import importlib.metadata
        distributions = list(importlib.metadata.distributions())
        try:
            self.rows = sorted(distributions, key=lambda d: d.name.lower())
        except AttributeError:  # Python == 3.9       distributions do not have .name attr, instead use .metadata.distributions['Name']
            for r in distributions:
                r.name = r.metadata['Name']
            self.rows = sorted(distributions, key=lambda d: d.name.lower())

    def openRow(self, row):
        'Open package metadata as Python object'
        return PyobjSheet(f'{row.name}-{row.version}', source=row)


BaseSheet.addCommand('', 'open-python-packages', 'vd.push(PythonPackagesSheet("python-packages"))', 'open Python Packages Sheet listing the installed packages')

vd.addMenuItems('''
    System > Python > installed packages > open-python-packages
''')

vd.addGlobals(PythonPackagesSheet=PythonPackagesSheet)
