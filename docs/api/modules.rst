
# Module abilities

Internal modules and external plugins can:

- define new commands
- add new options
- set existing options
- maintain state on vd singleton or sheets or columns
- add arbitrary Python code before/after most functions
- replace functions
- add new sheet types
- new file formats and urls
- have lazy dependencies (with vd.importExternal)

# Module imports

By default, VisiData loads all installed plugins and all of its own internal modules.
Some modules (esp loaders) may have dependencies in PyPI that aren't installed.

Modules must lazily import any external dependencies only when the feature or loader is attempted to be used.  i.e. modules must not import external dependencies at file scope.  For loaders this should happen in reload/iterload() instead of vd.open_foo, if possible.

The import should be with vd.importExternal so that VisiData can give a command to install the library via pip.

Some modules are not compatible with each other; for instance, the traditional visidata sqlite loader which loads all data into memory, and the vdsql sqlite loader which uses Ibis to compose SQL queries that get executed against the sqlite database itself.

The last module to be imported will have its functions registered for the filetype or command.  This should work fine for most cases (latter modules are generally more advanced), but to use the former module, this module must not be loaded in the first place.

