---
eleventyNavigation:
  key: Plugins
  order: 13
Updated: 2026-10-16
Version: VisiData 3.5
---

A *plugin* is an optional Python module to modify or extend VisiData functionality. Once installed, all plugins are automatically imported when `vd` is started.

# How to install a plugin

Plugins can be installed in 3 places:

1. They can come packaged with the VisiData install.
2. They can be installed via pip.
3. They can be copied into the `plugins/` subdirectory of the [VisiData directory](#the-visidata-directory).

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

Python modules in the [VisiData directory](#the-visidata-directory) (`<vd_dir>` below) are available for import from `.visidatarc`.

To install a plugin manually:

1. Make a `plugins` directory: `mkdir -p <vd_dir>/plugins`
2. Copy the plugin Python file there: `cp myplugin.py <vd_dir>/plugins`
3. Add a line to `~/.visidatarc` to import the plugin: `import plugins.myplugin`
4. Install the dependencies for the plugin (if any).

# How to Disable Plugins

The nuclear option is `--nothing` or `-N` flag, which forces the base configuration, not loading any .visidatarc or plugins.
This is especially useful for debugging; when filing an issue, please make sure the bug reproduces with `-N` (if not, it is likely something in your .visidatarc)

To load `.visidatarc` but not autoload plugins installed with pip, set `options.plugins_autoload` on the command-line:

    `vd --plugins-autoload=False`

Plugins explicitly imported in .visidatarc will still be installed.

# The VisiData directory

The VisiData directory holds local plugins (`plugins/`) and their dependencies (`plugins-deps/`), saved macros, Google API tokens, the HTTP cache for the scrape and reddit loaders, and REPL history.
VisiData adds it to the Python import path at startup.

The default VisiData directory is:

- Linux: `~/.config/visidata`
- macOS: `~/Library/Preferences/visidata`
- Windows: `%LOCALAPPDATA%\visidata\visidata`

On Linux and macOS, `XDG_CONFIG_HOME` changes the default to `$XDG_CONFIG_HOME/visidata`.

To use another directory, set the `VD_DIR` environment variable before starting `vd`, or pass `--visidata-dir=<vd_dir>` on the command line.
The command-line option takes precedence over `VD_DIR`.
For example, to use `~/.visidata`, add this to the shell startup file:

    export VD_DIR="$HOME/.visidata"

## Other storage locations

VisiData stores some files outside the VisiData directory.
`VD_DIR` and `--visidata-dir` do not move these.

- The data directory holds input history (`input_history.jsonl`) and the list of saved macros (`macros.jsonl`).
  Default: `~/.local/share/visidata` (Linux), `~/Library/Application Support/visidata` (macOS), `%LOCALAPPDATA%\visidata\visidata` (Windows), or `$XDG_DATA_HOME/visidata`.
- The cache directory holds cached downloads, like the message of the day and currency rates.
  Default: `~/.cache/visidata` (Linux), `~/Library/Caches/visidata` (macOS), `%LOCALAPPDATA%\visidata\visidata\Cache` (Windows), or `$XDG_CACHE_HOME/visidata`.
- The config file is `config.py` in the default VisiData directory if it exists, otherwise `~/.visidatarc`.
  Set `VD_CONFIG` or pass `--config=<file>` to use another file.

# VisiData API reference

For help making plugins, see the [VisiData API reference](https://visidata.org/docs/api).
