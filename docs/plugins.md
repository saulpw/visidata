---
eleventyNavigation:
  key: Plugins
  order: 13
Updated: 2023-11-22
Version: VisiData 3.0
---

A *plugin* is an optional Python module to modify or extend VisiData functionality. Once installed, all plugins are automatically imported when `vd` is started.

# How to install a plugin

Plugins can be installed in 3 places:

1. They can come packaged with the VisiData install.
2. They can be installed via pip.
3. They can be copied into the `.visidata/plugins/` directory.

## builtin plugins

The VisiData release includes additional functionality that isn't enabled by default, but which can be made available by importing the module.
For example, there are some features available in `visidata.experimental`, like `digit_autoedit`, which starts editing the current cell when a numeric digit is pressed (like Excel).
VisiData intentionally does not work this way, but people who prefer their terminal applications to act more like Excel can add this to their .visidatarc:

    import visidata.experimental.digit_autoedit

## via pip

Any package with a `visidata.plugins` entry point will be loaded automatically by default.
These plugins must be managed via pip (to upgrade or remove).
Plugins can be published to PyPI or downloaded as wheels or installed directly from source.

For example, `DarkDraw` is a VisiData plugin that allows drawing text-art.
Once the Python module is installed, you can use `vd` to open and save a `.ddw` file, which is a text image or animation specified in JSON format.
It also adds other commands and options.

## copied manually into local plugins directory

Finally, `.visidatarc` can import any Python code.
Since any Python modules in the `options.visidata_dir` directory (default `~/.visidata/`) are available for import,
you can copy a plugin into a module in that directory and import it that way.

To install a plugin manually:

1. Make a `plugins` directory: `mkdir -p ~/.visidata/plugins`
2. Copy the plugin Python file there: `cp myplugin.py ~/.visidata/plugins`
3. Add a line to your ~/.visidatarc to import the plugin: `import plugins.myplugin`
4. Install the dependencies for the plugin (if any).

# How to Disable Plugins

The nuclear option is `--nothing` or `-N` flag, which forces the base configuration, not loading any .visidatarc or plugins.
This is especially useful for debugging; when filing an issue, please make sure the bug reproduces with `-N` (if not, it is likely something in your .visidatarc)

To load `.visidatarc` but not autoload plugins installed with pip, set `options.plugins_autoload` on the command-line:

    `vd --plugins-autoload=False`

Plugins explicitly imported in .visidatarc will still be installed.

# VisiData API reference

For help making plugins, see the [VisiData API reference](https://visidata.org/docs/api).
