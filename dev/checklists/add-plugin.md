1. In the visidata repo under `plugins/`, create a `.py` file for the new plugin.
2. In that file add in all the code. For a plugin to be installable via `open-plugins`, they must be composed of a single file with additional dependencies installable via pip.
3. Ensure that the plugin has a `__version__`.
4. Add a row for the plugin, with all associated necessary informations, to `plugins/plugins.tsv`.
    - url: link to where the plugin file is hosted.
    - latest_ver: the current version of the plugin.
    - latest_release: the date the current version of the plugin was shipped.
    - author: your beautiful self.
    - visidata_ver: the latest version of visidata this plugin was tested on.
    - requirements (optional): For pip-installable dependencies. Separate each one by a space.
