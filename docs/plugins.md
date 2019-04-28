- Updated: 2019-03-05
- Version: VisiData 1.6

# Plugins

Plugins are optional Python modules that extend or modify base VisiData's functionality. Once configured, plugins will be available upon every `vd` launching.

# Known plugin homes

* [saulpw's repo](https://github.com/saulpw/visidata/tree/develop/plugins)
* [jsvine's repo](https://github.com/jsvine/visidata-plugins)
* [anjakefala's repo](https://github.com/anjakefala/vd-plugins)
* ...and [let us know](https://github.com/saulpw/visidata/issues/new) about yours! Some advice for [making plugins](https://github.com/saulpw/visidata/blob/develop/dev/checklists/add-plugin.md).

# How to use/activate a plugin

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

We maintain a list of plugins which can be downloaded and installed from within the application itself. To incorporate a plugin into this list, add it to [plugins.tsv](https://github.com/saulpw/visidata/blob/develop/plugins/plugins.tsv), and create a PR off of the `develop` branch.

* Press <kbd>Space</kbd>, and then type `open-plugins` to open the **PluginsSheet**.
* To download and install a plugin, move the cursor to its row and press `a` (add).
* To uninstall a plugin, move the cursor to its row and press `d` (delete).

Adding a plugin performs all the manual steps above, automatically.

Removing a plugin will delete its its import from `~/.visidatarc`. It will not remove the plugin itself from ~/.visidata nor any of its dependencies.
