---
eleventyNavigation:
  key: Plugins
  order: 13
Updated: 2019-03-05
Version: VisiData 1.6
---


Plugins are optional Python modules that extend or modify base VisiData's functionality. Once configured, plugins will be available upon every `vd` launching.

## Known plugin homes

* [saulpw's repo](https://github.com/saulpw/visidata/tree/develop/plugins)
* [jsvine's repo](https://github.com/jsvine/visidata-plugins)
* [anjakefala's repo](https://github.com/anjakefala/vd-plugins)
* [ajkerrigan's repo](https://github.com/ajkerrigan/visidata-plugins)
* ...and [let us know](https://github.com/saulpw/visidata/issues/new) about yours! Advice for [making plugins](https://visidata.org/docs/api).

# How to use/activate a plugin

## Manually

1. Make your plugin directory: `mkdir -p ~/.visidata/plugins`
2. Copy the plugin Python file there: `cp myplugin.py ~/.visidata/plugins` 
3. Add a line to your ~/.visidatarc to import the plugin: `import plugins.myplugin`
4. Install the dependencies for the plugin.

For plugins that the VisiData core maintenance team curates, the dependencies can be found in the `pydeps` attribute in the [plugins.json](https://visidata.org/plugins/plugins.jsonl).

For example, the plugin **vfake** contains commands for creating columns with anonymised data.

To install it

1. Copy `vfake/` from the [repo](https://github.com/saulpw/visidata/tree/develop/plugins) to `~/.visidata/plugins`.
2. Type `pip3 install faker` to install its dependency [faker](https://github.com/joke2k/faker).
3. Add `import plugins.vfake` to `~/.visidatarc`.

## From within VisiData

We maintain a list of plugins which can be downloaded and installed from within the application itself. To incorporate a plugin into this list, add it to [plugins.jsonl](https://raw.githubusercontent.com/visidata/dlc/stable/plugins.jsonl), and create a PR off of the `develop` branch.

To install a plugin, and its dependencies, from within VisiData:

1. Press <kbd>Space</kbd>, and then type `open-plugins` to open the **PluginsSheet**.

**or**

1. Launch the **vdmen** with `vd` on the commandline (do not provide a source). Press `Enter` on the row referencing the *plugins sheet*.
2. To download and install a plugin, move the cursor to its row and press `a` (add).
3. To uninstall a plugin, move the cursor to its row and press `d` (delete).

Adding a plugin performs all the manual steps above, automatically.

Removing a plugin will delete its import from `~/.visidata/plugins/__init__.py`. It will not remove the plugin itself from ~/.visidata nor any of its dependencies.
