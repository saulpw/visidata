1. In the visidata repo under `plugins/`, create a directory for the new plugin.
2. Add an `__init__.py` file, with all the code, and/or relative imports to other .py files in the directory.
3. Ensure that it has a `__version__` string at the top, like " ".
4. Create a file `VERSION` which will contain that same version number.
5. If the plugin has any dependencies, add them to a new `requirements.txt` in the directory.
6. Add a row for the plugin, with all associated necessary informations, to `plugins/plugins.tsv`.
