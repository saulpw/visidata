- Updated: 2019-03-05
- Version: VisiData 1.6

# Plugins

## Manually

1. Move the plugin module into `~/.visidata`.
2. Ensure its dependencies are installed.
3. Import the module within `~/.visidatarc`.

For example, the plugin **vfake** contains commands for creating columns with anonymised data.

To install it

1. Copy `vfake/` from the [repo](https://github.com/saulpw/visidata/tree/develop/plugins) to `~/.visidata`.
2. Type `pip3 install -r ~/.visidata/vfake/requirements.txt` (or `pip3 install faker`) to install its dependency [faker](https://github.com/joke2k/faker).
3. Add `from vfake import *` to `~/.visidatarc`.

## From within VisiData

visidata.org maintains a set of plugins which can be downloaded and installed from within the application itself.

* Press <kbd>Space</kbd>, and then type `open-plugins` to open the **PluginsSheet**.
* To add a plugin, move the cursor to its row and press `a`.
* To remove a plugin, move the cursor to its row and press `d`.

Adding a plugin performs all the manual steps above, automatically.

Removing a plugin will delete its directory from `~/.visidata` and its import from `~/.visidatarc`. It will not remove any of its dependencies.
