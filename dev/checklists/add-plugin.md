# Creating an external plugin

1. Put all of the Python code in a single .py file in your repo (or in `saulpw/visidata/plugins` for builtin optional plugins).
    - Ensure that the plugin has a `__version__`.

2. In a `plugins.jsonl` file in your repo, add a row for each plugin with all necessary informations:
    - `url`: link to where the plugin file is hosted.
    - `description`: link to where the plugin file is hosted.
    - `latest_ver`: the current version of the plugin.
    - `latest_release`: the date the current version of the plugin was shipped.
    - `maintainer`: your contact information.
    - `visidata_ver`: the latest version of visidata this plugin was tested on.
    - `pydeps` (optional): Space-separated list of pip-installable python modules required for the plugin.
    - `vdplugindeps` (optional): Space-separated list of vd plugin dependencies.
    - `sha256`: SHA256 hash of the contents of the plugin .py file for the `latest_release`.
